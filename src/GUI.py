import logging
import os
import platform
import re
import subprocess
import tkinter as tk
import tkinter.simpledialog
import xml.etree.ElementTree as ET
from tkinter import PhotoImage, filedialog, messagebox

import cairosvg
from graphviz import Digraph
from svg_parser import (
    check_state_type1,
    check_state_type2,
    find_active_states,
    get_elements,
    get_hierarchy,
    identify_xml_type,
    parse_svg,
    parse_svg2,
)

current_scale = 1.0
last_scale = None
last_svg_content_hash = None
debug_mode = False
xml_type = None
loaded_svg_content = None
MIN_WIDTH = 1
MIN_HEIGHT = 1
current_image = None
transition_trace = []
state_stack = []
is_svg_updated = False
hints_visible = False
current_state = {"active": [], "remembered": []}
transitions = {}


global transition_trace_label, transitions_file_path
transitions_file_path = None


def read_transitions_from_file(file_path):
    global transitions, current_state
    transitions = {}
    transition_counter = {}

    def add_transition(source, dest, label):
        source_key = file_state_representation(source)
        dest_key = file_state_representation(dest)

        if source_key not in transitions:
            transitions[source_key] = {}

        if dest_key not in transitions[source_key]:
            transitions[source_key][dest_key] = {label: "Option 1"}
        else:
            counter = transition_counter.get((source_key, dest_key), 1) + 1
            transition_counter[(source_key, dest_key)] = counter
            option_label = f"Option {counter}"
            transitions[source_key][dest_key][label] = option_label

    with open(file_path, "r") as file:
        for line in file.readlines():
            line = line.strip()

            if line.startswith("[*] -> "):
                state_str = line[6:].strip()
                active, remembered = parse_state(state_str)
                current_state["active"] = active
                current_state["remembered"] = remembered
                initial_state_key = file_state_representation(state_str)
                transitions[initial_state_key] = {}
            elif "->" in line:
                parts = line.split("->")
                source_str = parts[0].strip()
                dest_and_label = parts[1].strip()
                dest_str, label = map(str.strip, dest_and_label.split(":"))
                add_transition(source_str, dest_str, label)

    return current_state, transitions


def clean_state_representation(state):
    state = state.replace("[", "").replace("]", "").replace("''", "")
    state = state.strip()
    return state


def create_state_diagram_graph():
    global transitions, current_state
    graph = Digraph(comment="UML State Diagram")

    added_states = set()

    for source, dest_dict in transitions.items():
        cleaned_source = clean_state_representation(source)

        if cleaned_source not in added_states:
            graph.node(cleaned_source)
            added_states.add(cleaned_source)

        for dest, label_dict in dest_dict.items():
            cleaned_dest = clean_state_representation(dest)

            if cleaned_dest not in added_states:
                graph.node(cleaned_dest)
                added_states.add(cleaned_dest)

            for label, option_label in label_dict.items():
                graph.edge(cleaned_source, cleaned_dest, label=label)

    return graph


def show_state_diagram_graph():
    global transitions

    if not transitions:
        print("No transitions data available. Load transitions first.")
        return

    graph = create_state_diagram_graph()
    display_state_diagram_graph(graph)


def display_state_diagram_graph(graph):
    graph_file_path = "state_diagram_graph.dot"
    graph.save(graph_file_path)

    subprocess.run(["dot", "-Tpng", "-o", "state_diagram_graph.png", graph_file_path])

    image_path = os.path.abspath("state_diagram_graph.png")

    if platform.system() == "Darwin":
        subprocess.run(["open", "-a", "Preview", image_path])
    elif platform.system() == "Windows":
        os.startfile(image_path, "open")
    elif platform.system() == "Linux":
        subprocess.run(["xdg-open", image_path])
    else:
        print("Unsupported operating system.")


def on_canvas_click(
    event, canvas, transition_trace_label, reset_button, undo_button, parent
):
    global hints_visible
    try:
        ELEMENTS = get_elements()

        if not ELEMENTS:
            return

        x_offset = canvas.canvasx(0)
        y_offset = canvas.canvasy(0)
        x = (event.x + x_offset) / current_scale
        y = (event.y + y_offset) / current_scale
        clicked_state = None

        if xml_type == "Type1":
            clicked_state = check_state_type1(x, y)
        elif xml_type == "Type2":
            state_hierarchy = check_state_type2(x, y)
            if state_hierarchy:
                clicked_state = state_hierarchy[-1]
        else:
            print("Unknown XML type")
            return

        state_transitioned = state_parameter(
            clicked_state, transition_trace_label, reset_button, undo_button, parent
        )

        show_popup(clicked_state, x, y)
        if state_transitioned:
            render_uml_diagram(
                canvas,
                svg_file_path,
                debug_mode=debug_mode,
            )
        else:
            print("No need to call render_uml_diagram")
    except Exception as e:
        logging.error("Error in on_canvas_click: %s", str(e))


def state_parameter(state, transition_trace_label, reset_button, undo_button, parent):
    global hints_visible
    print(f"ON CANVAS CLICKED STATE: {state}")

    current_active_formatted = ",".join(current_state["active"])
    current_remembered_formatted = (
        ",".join(current_state["remembered"]) if current_state["remembered"] else None
    )

    if current_remembered_formatted:
        combined_transition_state = (
            f"{state}({current_active_formatted},{current_remembered_formatted})"
        )
    else:
        combined_transition_state = state

    print(f"combined_transition_state: {combined_transition_state}")

    available_transitions = transitions.get(9, {})

    if current_state["remembered"] == []:
        combined_transition_state = f"{state}({current_state['active']})"

        for transition in available_transitions:
            print(f"ON CANVAS 1: {transition}")
        if combined_transition_state in available_transitions:
            print("ON CANVAS 1 - CASE 1")
            hints_visible = False
            state_transitioned = state_handling(
                combined_transition_state,
                transition_trace_label,
                reset_button,
                undo_button,
                parent,
            )
        else:
            print("ON CANVAS 1 - CASE 2")
            hints_visible = False
            state_transitioned = state_handling(
                state,
                transition_trace_label,
                reset_button,
                undo_button,
                parent,
            )
    else:
        combined_transition_state = f"{state}({current_state['remembered']})"
        current = state_representation(current_state)

        print(
            f"ON CANVAS 2 TEST 3: combined_transition_state: {combined_transition_state} From current state : {current}"
        )

        for transition in transitions.get(current, {}):
            print(f"ON CANVAS 2: {transition}")

        if combined_transition_state in transitions.get(current, {}):
            print("ON CANVAS 2 - CASE 1")
            hints_visible = False
            state_transitioned = state_handling(
                combined_transition_state,
                transition_trace_label,
                reset_button,
                undo_button,
                parent,
            )
        else:
            print("ON CANVAS 2 - CASE 2")
            hints_visible = False
            state_transitioned = state_handling(
                state,
                transition_trace_label,
                reset_button,
                undo_button,
                parent,
            )

    return state_transitioned


def state_handling(state, transition_trace_label, reset_button, undo_button, parent):
    global current_state, transition_trace
    STATE_HIERARCHY = get_hierarchy()

    state_changed = False

    def collect_all_children(state_name, hierarchy):
        all_children = []
        children = hierarchy.get(state_name, [])
        for child in children:
            print(f"CHILD TEST: {child}")
            all_children.append(child)
            all_children.extend(collect_all_children(child, hierarchy))

        for element in all_children:
            if hierarchy.get(element):
                all_children.remove(element)

        return all_children

    def is_part_of_combined_state(clicked_state, allowed_transitions):
        for transition_state in allowed_transitions:
            active_transition_states, _ = parse_state(transition_state)
            for active_state in active_transition_states:
                individual_states = active_state.split(",")
                if clicked_state in individual_states:
                    return transition_state
        return None

    current = current_state

    current = state_representation(current_state)
    print(f"Current State : {current}")
    print(f"Clicked State : {state}")
    print("============================")

    active_clicked, remembered_clicked = parse_state(state)
    active_current, remembered_current = parse_state(current)

    children = collect_all_children(state, STATE_HIERARCHY)
    print(f"Children : {children}")

    if state != "Outside":
        allowed_transitions = transitions.get(current, {})
        print(
            f"Clicked State: {state}, Allowed Transitions from {current}: {allowed_transitions}"
        )

        transition_state = is_part_of_combined_state(
            state, transitions.get(current, {})
        )
        print(f"Transition state after checking combined states: {transition_state}")

        print(f"state: {state} in allowed_transitions: {allowed_transitions}")
        if transition_state in transitions.get(current, {}):
            print(
                f"Transition state after checking combined states: {transition_state}"
            )
            chosen_transition = None
            if isinstance(transitions[current][transition_state], dict):
                chosen_transition = ask_user_for_transition(
                    transitions[current][transition_state], parent
                )
            else:
                chosen_transition = transitions[current][transition_state]

            if chosen_transition is not None:
                print(f"Handling transition to combined state {transition_state}")
                state_stack.append(current_state.copy())
                active_next, remembered_next = parse_state(transition_state)
                if (
                    "," in active_next[0]
                ):
                    active_next = active_next[0].split(",")
                current_state["active"] = active_next
                current_state["remembered"] = remembered_next
                transition_trace.append(chosen_transition)
                update_transition_display(
                    transition_trace_label, reset_button, undo_button
                )
                state_changed = True
                print(f"Transition: {current_state}")
                return state_changed

        if state in allowed_transitions:
            if isinstance(allowed_transitions[state], dict):
                chosen_transition = ask_user_for_transition(
                    allowed_transitions[state], parent
                )
            else:
                chosen_transition = allowed_transitions[state]

            if chosen_transition is not None:
                print(f"CASE 1 - Handling dictionary transition {state}")
                state_stack.append(current_state.copy())
                if active_clicked != active_current:
                    state_changed = True
                    print("STATE CHANGED")
                current_state["active"] = active_clicked
                current_state["remembered"] = remembered_clicked
                transition_trace.append(chosen_transition)
                update_transition_display(
                    transition_trace_label, reset_button, undo_button
                )
                print(f"Transition: {current_state}")
        elif state in allowed_transitions:
            print(f"CASE 2 - Handling direct transition {active_clicked}")
            state_stack.append(current_state.copy())
            if active_clicked != active_current:
                state_changed = True
                print("STATE CHANGED")
            current_state["active"] = active_clicked
            current_state["remembered"] = remembered_clicked
            transition_trace.append(allowed_transitions[state])
            update_transition_display(transition_trace_label, reset_button, undo_button)
            print(f"Transition: {current_state}")
        elif state in STATE_HIERARCHY and children != []:
            print(
                f"CASE 3 - Handling transition from complex or hierarchical state: {active_current}"
            )
            allowed_transitions_from_children = {}

            for child in children:
                if child in allowed_transitions:
                    child_transitions = allowed_transitions[child]
                    if isinstance(child_transitions, dict):
                        for option, transition_label in child_transitions.items():
                            option_key = option
                            print(f"Child: {child} - Transition_label: {option}")
                            allowed_transitions_from_children[option_key] = child
                else:
                    allowed_transitions_from_children[child_transitions] = child
                print(
                    f"allowed_transitions_from_children: {allowed_transitions_from_children}"
                )

            if allowed_transitions_from_children:
                chosen_transition = ask_user_for_transition(
                    allowed_transitions_from_children, parent
                )
                if chosen_transition is not None:
                    state_stack.append(current_state.copy())
                    next_state = allowed_transitions_from_children[chosen_transition]
                    print(f"Chooen next state: {next_state}")
                    active, new_remembered = parse_state(next_state)
                    if active != active_current:
                        state_changed = True
                        print("STATE CHANGED")
                    current_state["active"] = active
                    current_state["remembered"] = new_remembered
                    transition_trace.append(chosen_transition)
                    update_transition_display(
                        transition_trace_label, reset_button, undo_button
                    )
        else:
            print(f"No valid transitions found from {current} to {active_clicked}")
            messagebox.showinfo(
                "Invalid Transition",
                f"Cannot transition from {current} to {state}",
            )
            print("Invalid transition. Ignoring click.")
    else:
        messagebox.showinfo("Clicked Outside", "Please choose a valid state")
        print("Outside")

    return state_changed


def parse_state(state_str):
    if "(" in state_str and ")" in state_str:
        parts = state_str.split("(")
        parts[1] = parts[1].strip(")")
        print(f"Parts of state_str: {parts}")

        if parts[0] == "":
            active = parts[1].strip("()").split(", ") if parts[1].strip("()") else []
            remembered = (
                parts[0].strip("()").split(", ")
                if len(parts) > 1 and parts[0].strip("()")
                else []
            )
        else:
            active = parts[0].strip("()").split(", ") if parts[0].strip("()") else []
            remembered = (
                parts[1].strip("()").split(", ")
                if len(parts) > 1 and parts[1].strip("()")
                else []
            )

        print(f"Active: {active}, Remembered: {remembered}")
    else:
        active = state_str.split(", ") if "," in state_str else [state_str]
        remembered = []

        print(f"Active: {active}, Remembered: {remembered}")

    return active, remembered


def state_representation(state):
    active = state["active"]
    remembered = state["remembered"]
    if not remembered:
        return f"{','.join(active)}"
    else:
        return f"{','.join(active)}({', '.join(remembered)})"


def file_state_representation(state):
    active, remembered = parse_state(state)

    if active:
        for element in active:
            print(f"active element: {element}")

    if remembered:
        for element in remembered:
            print(f"remembered element: {element}")

    active_str = ",".join(active) if active else ""
    remembered_str = ",".join(remembered) if remembered else ""

    if remembered_str:
        return f"{active_str}({remembered_str})"
    else:
        return active_str


class TransitionDialog(tk.Toplevel):
    def __init__(self, parent, transitions_dict):
        super().__init__(parent)
        self.trans_value = tk.StringVar()
        self.selected_option = None

        options = list(transitions_dict.items())

        if "" in transitions_dict:
            transitions_dict[" "] = transitions_dict[""]
            del transitions_dict[""]

        if len(options) == 1:
            self.selected_option = options[0][0]
            self.destroy()
            return

        first_key = next(iter(transitions_dict)) if transitions_dict else None
        if first_key:
            self.trans_value.set(first_key)

        radio_button_font = ("Verdana", 9)

        label = tk.Label(
            self,
            text="Select one of the following transitions:",
            font=radio_button_font,
        )
        label.pack(pady=(10, 5), padx=25)

        for key, label in transitions_dict.items():
            radio_button = tk.Radiobutton(
                self,
                text=key,
                variable=self.trans_value,
                value=key,
                font=radio_button_font,
            )
            radio_button.pack(anchor=tk.W, pady=5, padx=50)

        ok_button = tk.Button(
            self, text="OK", command=self.on_ok, font=radio_button_font
        )
        ok_button.pack(padx=20, pady=(50, 10))

        self.center_window()

        self.wait_window(self)

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def on_ok(self):
        self.selected_option = self.trans_value.get()
        self.destroy()


def ask_user_for_transition(transitions_dict, parent):
    dialog = TransitionDialog(parent, transitions_dict)
    return dialog.selected_option


def update_transition_display(transition_trace_label, reset_button, undo_button):
    global transition_trace
    formatted_trace = [str(transition) for transition in transition_trace]

    if formatted_trace:
        formatted_text = "Transition Trace: " + ", ".join(formatted_trace) + ", "
    else:
        formatted_text = "Transition Trace: "

    transition_trace_label.config(text=formatted_text)

    reset_button["state"] = "normal" if transition_trace else "disabled"
    undo_button["state"] = "normal" if transition_trace else "disabled"


def show_popup(message, x, y):
    if debug_mode:
        popup = tk.Toplevel()
        popup.title("Information")
        label_coords = tk.Label(popup, text=f"Clicked Coordinates (x, y): ({x}, {y})")
        label_state = tk.Label(popup, text=f"State: {message}")
        label_coords.pack()
        label_state.pack()


def get_modified_svg_content():
    global svg_file_path, svg_rainbow_file_path
    if debug_mode:
        selected_svg_file = svg_rainbow_file_path
    else:
        selected_svg_file = svg_file_path

    if selected_svg_file and os.path.exists(selected_svg_file):
        with open(selected_svg_file, "r") as svg_file:
            return svg_file.read()
    else:
        return None


def get_svg_dimensions(svg_content, max_dimension=10000):
    root = ET.fromstring(svg_content)
    width = height = None

    if "width" in root.attrib and "height" in root.attrib:
        width = float(re.sub(r"[^\d.]", "", root.attrib["width"]))
        height = float(re.sub(r"[^\d.]", "", root.attrib["height"]))
    elif "viewBox" in root.attrib:
        viewBox = [float(v) for v in root.attrib["viewBox"].split()]
        width, height = viewBox[2], viewBox[3]
    else:
        raise ValueError("SVG dimensions could not be determined.")

    while width > max_dimension or height > max_dimension:
        width /= 1.5
        height /= 1.5
        print("Reducing dimensions to fit within the maximum allowed size.")

    print(f"Adjusted SVG Width: {width}, Adjusted SVG Height: {height}")

    return width, height


def render_uml_diagram(canvas, svg_file_path, debug_mode):
    global loaded_svg_content, last_svg_content_hash, last_scale, current_scale, current_image, is_svg_updated
    global original_width, original_height
    print("Rendering UML diagram using existing content.")
    ELEMENTS = get_elements()
    STATE_HIERARCHY = get_hierarchy()
    canvas.delete("all")
    if not svg_file_path:
        print("No SVG file selected.")
        return

    modified_svg_content = loaded_svg_content

    target_width = original_width * current_scale
    target_height = original_height * current_scale

    target_width = max(target_width, MIN_WIDTH)
    target_height = max(target_height, MIN_HEIGHT)

    def split_states(state_list):
        states = []
        for state in state_list:
            states.extend(state.split(","))
        return states

    if modified_svg_content:
        if (
            current_scale * max(ELEMENTS, key=lambda item: item[1][1])[1][1] < MIN_WIDTH
            or current_scale * max(ELEMENTS, key=lambda item: item[1][3])[1][3]
            < MIN_HEIGHT
        ):
            print("SVG dimensions too small for rendering.")
            return

        if is_svg_updated or current_scale != last_scale:
            png_data = cairosvg.svg2png(
                bytestring=loaded_svg_content,
                output_width=target_width,
                output_height=target_height,
            )
            image = PhotoImage(data=png_data)
            current_image = image

            print(f"Resizing to Width: {target_width}, Height: {target_height}")
            canvas.delete("all")
            canvas.create_image(0, 0, anchor="nw", image=image)
            canvas.image = image

            is_svg_updated = False
            last_scale = current_scale
        else:
            if current_image is not None:
                canvas.delete("all")
                canvas.create_image(0, 0, anchor="nw", image=current_image)
            else:
                print("No current image to render.")

        if not ELEMENTS:
            print("No elements to highlight. Only Rendering the SVG")
            return

        print(f"before state_representation,current_state: {current_state} ")
        current = state_representation(current_state)
        print(f"after state_representation,current_state: {current} ")
        active_states, remembered_states = parse_state(current)
        print(f"Active States: {active_states}, Remembered States: {remembered_states}")

        for active_state in split_states(active_states):
            active_state = active_state.strip()
            marked_states = find_active_states(active_state)
            print(f"Marked active state: {active_state}, Coordinates: {marked_states}")
            print("STATE_HIERARCHY Condition reached")
            for state, hierarchy in STATE_HIERARCHY.items():
                if state == active_state or state in marked_states:
                    print("STATE_HIERARCHY Condition :  condition passed")
                    print(f"Highlighting active state: {active_state}")
                    for element in ELEMENTS:
                        print(f"Element[0] (active): {element[0]}, state: {state}")
                        if element[0] == state:
                            x1, x2, y1, y2 = [
                                int(coord * current_scale) for coord in element[1]
                            ]
                            outline_color = (
                                "red" if state != active_state else "turquoise"
                            )
                            outline_width = 2 if state != active_state else 3
                            canvas.create_rectangle(
                                x1,
                                y1,
                                x2,
                                y2,
                                outline=outline_color,
                                width=outline_width,
                            )
                            print(
                                f"Highlighting active state: {state} at {x1, y1, x2, y2}"
                            )

        for remembered_state in split_states(remembered_states):
            remembered_state = remembered_state.strip()
            print(f"Highlighting remembered state: {remembered_state}")
            for element in ELEMENTS:
                if element[0] == remembered_state:
                    x1, x2, y1, y2 = [
                        int(coord * current_scale) for coord in element[1]
                    ]
                    canvas.create_rectangle(x1, y1, x2, y2, outline="#AFEEEE", width=2)

        canvas.config(width=target_width, height=target_height)
        canvas.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))


def enter_state(
    state_name, canvas, transition_trace_label, reset_button, undo_button, parent
):
    global hints_visible
    state_transitioned = state_parameter(
        state_name, transition_trace_label, reset_button, undo_button, parent
    )

    if state_transitioned:
        render_uml_diagram(
            canvas,
            svg_file_path,
            debug_mode=debug_mode,
        )
    else:
        print("No need to call render_uml_diagram")


def highlight_next_states(canvas, next_states):
    global current_scale, hints_visible
    print("Highlighting next states:", next_states)
    ELEMENTS = get_elements()

    current = state_representation(current_state)
    active_current, _ = parse_state(current)

    split_current_states = set()
    for state in active_current:
        split_current_states.update(state.split(","))

    active_states = set()
    for state in next_states:
        active, _ = parse_state(state)
        for individual_state in active:
            active_states.update(individual_state.split(","))

    active_states = active_states - split_current_states

    canvas.delete("hints")

    for state, coordinates in ELEMENTS:
        if state in active_states:
            x1, x2, y1, y2 = [int(coord * current_scale) for coord in coordinates]
            state_width = x2 - x1
            state_height = y2 - y1
            state_center_x = (x1 + x2) / 2
            state_center_y = (y1 + y2) / 2

            oval_half_width = state_width / 2
            oval_half_height = state_height / 2

            canvas.create_oval(
                state_center_x - oval_half_width,
                state_center_y - oval_half_height,
                state_center_x + oval_half_width,
                state_center_y + oval_half_height,
                outline="orange",
                width=2,
                tags="hints",
            )
    if hints_visible:
        canvas.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))


def choose_file(canvas, transition_trace_label, reset_button, undo_button):
    global svg_file_path, xml_type, svg_rainbow_file_path, loaded_svg_content, current_state, transitions
    global is_svg_updated, original_width, original_height, transitions_file_path
    ELEMENTS = get_elements()
    STATE_HIERARCHY = get_hierarchy()

    file_path = filedialog.askopenfilename(
        filetypes=[("SVG files", "*.svg"), ("Text files", "*.txt")]
    )
    if not file_path:
        return False

    _, extension = os.path.splitext(file_path)

    if extension == ".svg":
        svg_file_path = file_path
        if "_rainbow.svg" in svg_file_path:
            svg_rainbow_file_path = svg_file_path
            svg_file_path = svg_rainbow_file_path.replace("_rainbow.svg", ".svg")
        else:
            svg_rainbow_file_path = svg_file_path.replace(".svg", "_rainbow.svg")
        transitions_file_path = svg_file_path.replace(".svg", "_flattened.txt")
    elif extension == ".txt":
        transitions_file_path = file_path
        svg_rainbow_file_path = transitions_file_path.replace(
            "_flattened.txt", "_rainbow.svg"
        )
        svg_file_path = svg_rainbow_file_path.replace("_rainbow.svg", ".svg")
    else:
        print("Unsupported file type.")
        return False

    if (
        not os.path.isfile(svg_file_path)
        or not os.path.isfile(svg_rainbow_file_path)
        or not os.path.isfile(transitions_file_path)
    ):
        print("You don't have all file types needed.")
        return False

    transitions_file_path = transitions_file_path

    loaded_svg_content = get_modified_svg_content()
    if loaded_svg_content:
        current_state = {"active": None, "remembered": None}
        transition_trace.clear()
        state_stack.clear()
        update_transition_display(transition_trace_label, reset_button, undo_button)
        clear_hints(canvas)
        global hints_visible
        hints_visible = False
        is_svg_updated = True
        original_width, original_height = get_svg_dimensions(loaded_svg_content)
    print("Loaded new SVG content.")
    tree = ET.parse(svg_rainbow_file_path)
    root = tree.getroot()
    xml_type = identify_xml_type(root)

    if xml_type == "Type1":
        print("Handling Type 1 XML.")
        canvas.delete("all")
        ELEMENTS.clear()
        STATE_HIERARCHY.clear()
        parse_svg(svg_rainbow_file_path)
    elif xml_type == "Type2":
        print("Handling Type 2 XML.")
        canvas.delete("all")
        ELEMENTS.clear()
        STATE_HIERARCHY.clear()
        parse_svg2(svg_rainbow_file_path)
    else:
        print("Unknown file type")
        return False

    current_state, transitions = read_transitions_from_file(transitions_file_path)

    print("Current State:", current_state)
    print("Transitions:", transitions)

    if ELEMENTS:
        max_x = max(state[1][1] for state in ELEMENTS)
        max_y = max(state[1][3] for state in ELEMENTS)
        canvas.config(width=max_x + 20, height=max_y + 20)

    render_uml_diagram(
        canvas,
        svg_file_path,
        debug_mode=debug_mode,
    )
    canvas.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))
    return True


def on_canvas_scroll(event, canvas):
    shift = (event.state & 0x1) != 0
    if shift:
        if event.delta > 0:
            canvas.xview_scroll(-1, "units")
        elif event.delta < 0:
            canvas.xview_scroll(1, "units")
    else:
        if event.delta > 0:
            canvas.yview_scroll(-1, "units")
        elif event.delta < 0:
            canvas.yview_scroll(1, "units")


def zoom(event, canvas):
    if event.state & 0x4:
        ELEMENTS = get_elements()
        global current_scale
        scale_factor = 1.1 if event.delta > 0 else 0.9

        new_scale = current_scale * scale_factor

        if (
            new_scale * max(ELEMENTS, key=lambda item: item[1][1])[1][1] < MIN_WIDTH
            or new_scale * max(ELEMENTS, key=lambda item: item[1][3])[1][3] < MIN_HEIGHT
        ):
            print("Zoom limit reached.")
            return

        current_scale = new_scale
        canvas.scale("all", event.x, event.y, scale_factor, scale_factor)

        scroll_x1, scroll_y1, scroll_x2, scroll_y2 = canvas.bbox("all")
        if (
            scroll_x1 is not None
            and scroll_y1 is not None
            and scroll_x2 is not None
            and scroll_y2 is not None
        ):
            canvas.config(scrollregion=(scroll_x1, scroll_y1, scroll_x2, scroll_y2))

        render_uml_diagram(
            canvas,
            svg_file_path,
            debug_mode=debug_mode,
        )
        if hints_visible:
            current = state_representation(current_state)
            next_states = transitions.get(current, {}).keys()
            highlight_next_states(canvas, next_states)


def maximize_visible_canvas(canvas):
    ELEMENTS = get_elements()
    global current_scale
    if not svg_file_path or not ELEMENTS:
        return

    canvas.update_idletasks()
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()

    print(f"Canvas Width: {canvas_width}, Canvas Height: {canvas_height}")

    diagram_width = max(state[1][1] for state in ELEMENTS)
    diagram_height = max(state[1][3] for state in ELEMENTS)

    print(f"Diagram Width: {diagram_width}, Diagram Height: {diagram_height}")

    if diagram_width <= 0 or diagram_height <= 0:
        print("Invalid diagram dimensions.")
        return

    width_zoom = max(canvas_width / diagram_width, 0.01)
    height_zoom = max(canvas_height / diagram_height, 0.01)

    proposed_scale = min(width_zoom, height_zoom)

    if (diagram_width * proposed_scale < MIN_WIDTH) or (
        diagram_height * proposed_scale < MIN_HEIGHT
    ):
        min_width_scale = MIN_WIDTH / diagram_width
        min_height_scale = MIN_HEIGHT / diagram_height
        current_scale = max(min_width_scale, min_height_scale)
    else:
        current_scale = proposed_scale

    render_uml_diagram(
        canvas,
        svg_file_path,
        debug_mode=debug_mode,
    )

    canvas.yview_moveto(0)
    canvas.xview_moveto(0)
    if hints_visible:
        current = state_representation(current_state)
        next_states = transitions.get(current, {}).keys()
        highlight_next_states(canvas, next_states)


def toggle_color_mode(canvas):
    global debug_mode, loaded_svg_content

    debug_mode = not debug_mode

    loaded_svg_content = get_modified_svg_content()

    print(f"Loaded SVG Content Updated: {loaded_svg_content is not None}")

    if loaded_svg_content:
        render_uml_diagram(
            canvas,
            svg_file_path,
            debug_mode=debug_mode,
        )


def show_hints(canvas):
    global current_state, transitions, hints_visible

    print("Show hints called")

    current_state_hints = state_representation(current_state)
    print(f"Show hints [current_state_hints]: {current_state_hints}")
    next_states = transitions.get(current_state_hints, {}).keys()
    print(f"Next states of {current_state_hints}:", next_states)

    clear_hints(canvas)

    if next_states and not hints_visible:
        highlight_next_states(canvas, next_states)
        hints_visible = True
    elif not next_states:
        messagebox.showinfo("No More Steps", "No more further steps are possible.")
        hints_visible = False
    elif hints_visible:
        clear_hints(canvas)
        hints_visible = False


def clear_hints(canvas):
    print("Clearing hints")
    canvas.delete("hints")


def reset_trace(transition_trace_label, reset_button, undo_button, canvas):
    global transition_trace, current_state, state_stack, hints_visible

    if state_stack:
        current_state = state_stack[0].copy()
    else:
        current_state = {"active": None, "remembered": None}

    state_stack.clear()

    transition_trace = []

    clear_hints(canvas)
    hints_visible = False

    update_transition_display(transition_trace_label, reset_button, undo_button)
    render_uml_diagram(
        canvas,
        svg_file_path,
        debug_mode=debug_mode,
    )
    print("Transition trace reset.")


def undo_last_transition(transition_trace_label, reset_button, undo_button, canvas):
    global current_state, transition_trace, state_stack, hints_visible

    if transition_trace:
        if state_stack:
            previous_state = state_stack.pop()
            current_state = previous_state.copy()
        else:
            current_state = {"active": None, "remembered": None}

        if previous_state:
            transition_trace.pop()

            update_transition_display(transition_trace_label, reset_button, undo_button)

            render_uml_diagram(
                canvas,
                svg_file_path,
                debug_mode=debug_mode,
            )

            undo_button["state"] = "normal"
            clear_hints(canvas)
            hints_visible = False
        else:
            print("State stack is empty.")
            messagebox.showinfo("No Undo Available", "No further undo is possible.")
            undo_button["state"] = "disabled"
    else:
        print("No transitions to undo.")
        messagebox.showinfo("No Undo Available", "No further undo is possible.")
        undo_button["state"] = "disabled"
