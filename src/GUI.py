import logging
import os
import re
import tkinter as tk
import tkinter.simpledialog
import xml.etree.ElementTree as ET
from tkinter import PhotoImage, filedialog, messagebox

import cairosvg
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


global transition_trace_label


def read_transitions_from_file(file_path):
    transitions = {}
    current_state = None
    transition_counter = {}

    with open(file_path, "r") as file:
        for line in file.readlines():
            line = line.strip()

            if line.startswith("[*] -> "):
                current_state = line[6:].strip()
                transitions[current_state] = {}
            elif "->" in line:
                parts = line.split("->")
                source = current_state if not parts[0].strip() else parts[0].strip()
                dest_and_label = parts[1].strip()
                dest, label = map(str.strip, dest_and_label.split(":"))

                if source not in transitions:
                    transitions[source] = {}

                if dest not in transitions[source]:
                    transitions[source][dest] = {label: "Option 1"}
                else:
                    counter = transition_counter.get((source, dest), 1)
                    transition_counter[(source, dest)] = counter + 1
                    option_label = f"Option {counter}"
                    transitions[source][dest][label] = option_label

    return current_state, transitions


def on_canvas_click(
    event, canvas, transition_trace_label, reset_button, undo_button, parent
):
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
        if clicked_state != current_state:
            state_handling(
                clicked_state, transition_trace_label, reset_button, undo_button, parent
            )

        show_popup(clicked_state, x, y)
        render_uml_diagram(
            canvas, svg_file_path, active_state=current_state, debug_mode=debug_mode
        )
    except Exception as e:
        logging.error("Error in on_canvas_click: %s", str(e))


def state_handling(state, transition_trace_label, reset_button, undo_button, parent):
    global current_state, transition_trace
    STATE_HIERARCHY = get_hierarchy()

    if state != "Outside":
        allowed_transitions = transitions.get(current_state, {})
        print(f"Clicked State: {state}, Allowed Transitions: {allowed_transitions}")

        if state in allowed_transitions and isinstance(
            allowed_transitions[state], dict
        ):
            print("Handling dictionary transition")
            chosen_transition = ask_user_for_transition(
                allowed_transitions[state], parent
            )

            if chosen_transition is not None:
                state_stack.append(current_state)
                current_state = state
                transition_trace.append(chosen_transition)
                update_transition_display(
                    transition_trace_label, reset_button, undo_button
                )
                print(f"Transition: {current_state}")
        elif state in allowed_transitions:
            print("Handling direct transition")
            state_stack.append(current_state)
            current_state = state
            transition_trace.append(allowed_transitions[state])
            update_transition_display(transition_trace_label, reset_button, undo_button)
            print(f"Transition: {current_state}")
        else:
            if state in STATE_HIERARCHY:
                print("Handling compound state transition")
                children = STATE_HIERARCHY[state]
                print(f"children: {children}")

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
                        state_stack.append(current_state)
                        next_state = allowed_transitions_from_children[
                            chosen_transition
                        ]
                        print(f"next state: {next_state}")
                        current_state = next_state
                        transition_trace.append(chosen_transition)
                        update_transition_display(
                            transition_trace_label, reset_button, undo_button
                        )
                        print(f"Transition: {current_state}")
                else:
                    print("Handling invalid transition")
                    messagebox.showinfo(
                        "Invalid Transition",
                        f"Cannot transition from {current_state} to {state}",
                    )
                    print("Invalid transition. Ignoring click.")
    else:
        messagebox.showinfo("Clicked Outside", "Please choose a valid state")
        print("Outside")


class TransitionDialog(tk.Toplevel):
    def __init__(self, parent, transitions_dict):
        super().__init__(parent)
        self.trans_value = tk.StringVar()
        self.selected_option = None

        options = list(transitions_dict.items())
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
    formatted_text = "Transition Trace: " + " , ".join(formatted_trace)
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


def render_uml_diagram(canvas, svg_file_path, active_state, debug_mode):
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

        if active_state is None:
            active_state = current_state

        marked_states = find_active_states(active_state)
        for state, hierarchy in STATE_HIERARCHY.items():
            if state == active_state or state in marked_states:
                for element in ELEMENTS:
                    if element[0] == state:
                        x1, x2, y1, y2 = [
                            int(coord * current_scale) for coord in element[1]
                        ]
                        outline_color = "red" if state != active_state else "green"
                        outline_width = 2 if state != active_state else 3
                        canvas.create_rectangle(
                            x1,
                            y1,
                            x2,
                            y2,
                            outline=outline_color,
                            width=outline_width,
                        )
                        break
        canvas.config(width=target_width, height=target_height)
        canvas.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        if active_state:
            marked_states = find_active_states(active_state)
            for state, hierarchy in STATE_HIERARCHY.items():
                if state == active_state or state in marked_states:
                    for element in ELEMENTS:
                        if element[0] == state:
                            x1, x2, y1, y2 = [
                                int(coord * current_scale) for coord in element[1]
                            ]
                            outline_color = "red" if state != active_state else "green"
                            outline_width = 2 if state != active_state else 3
                            canvas.create_rectangle(
                                x1,
                                y1,
                                x2,
                                y2,
                                outline=outline_color,
                                width=outline_width,
                            )
                            break

            canvas.config(width=target_width, height=target_height)
            canvas.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))


def enter_state(
    state_name, canvas, transition_trace_label, reset_button, undo_button, parent
):
    if state_name != current_state:
        state_handling(
            state_name, transition_trace_label, reset_button, undo_button, parent
        )
    marked_states = find_active_states(state_name)
    print(f"Marked states: {marked_states}")
    render_uml_diagram(
        canvas, svg_file_path, active_state=current_state, debug_mode=debug_mode
    )


def highlight_next_states(canvas, next_states):
    global current_scale
    print("Highlighting next states:", next_states)
    ELEMENTS = get_elements()
    for state, coordinates in ELEMENTS:
        if state in next_states:
            x1, x2, y1, y2 = [int(coord * current_scale) for coord in coordinates]
            canvas.create_rectangle(x1, y1, x2, y2, outline="yellow", width=2)


def choose_file(canvas):
    global svg_file_path, xml_type, svg_rainbow_file_path, loaded_svg_content, current_state, transitions
    global is_svg_updated, original_width, original_height
    ELEMENTS = get_elements()
    STATE_HIERARCHY = get_hierarchy()

    svg_file_path = filedialog.askopenfilename(filetypes=[("SVG files", "*.svg")])
    if not svg_file_path:
        return False

    print("Selected SVG File:", svg_file_path)

    transitions_file_path = filedialog.askopenfilename(
        filetypes=[("Text files", "*.txt")]
    )
    if not transitions_file_path:
        return False

    print("Selected Transitions File:", transitions_file_path)

    if svg_file_path.endswith("_rainbow.svg"):
        svg_rainbow_file_path = svg_file_path
        svg_file_path = svg_file_path.replace("_rainbow.svg", ".svg")
    else:
        svg_rainbow_file_path = svg_file_path.replace(".svg", "_rainbow.svg")

    if not os.path.isfile(svg_file_path) or not os.path.isfile(svg_rainbow_file_path):
        print("You don't have both file types needed.")
        return False

    loaded_svg_content = get_modified_svg_content()
    if loaded_svg_content:
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

    render_uml_diagram(canvas, svg_file_path, active_state=None, debug_mode=debug_mode)
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

        next_states = transitions.get(current_state, {}).keys()
        highlight_next_states(canvas, next_states)

        render_uml_diagram(
            canvas, svg_file_path, active_state=current_state, debug_mode=debug_mode
        )


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
        canvas, svg_file_path, active_state=current_state, debug_mode=debug_mode
    )

    canvas.yview_moveto(0)
    canvas.xview_moveto(0)


def toggle_color_mode(canvas):
    global debug_mode, loaded_svg_content

    debug_mode = not debug_mode

    loaded_svg_content = get_modified_svg_content()

    print(f"Loaded SVG Content Updated: {loaded_svg_content is not None}")

    if loaded_svg_content:
        render_uml_diagram(
            canvas, svg_file_path, active_state=None, debug_mode=debug_mode
        )


def show_hints(canvas):
    global current_state, transitions
    print("Show hints called")
    next_states = transitions.get(current_state, {}).keys()
    print("Next states:", next_states)
    highlight_next_states(canvas, next_states)


def reset_trace(transition_trace_label, reset_button, undo_button, canvas):
    global transition_trace, current_state
    transition_trace = []
    current_state = "A"
    update_transition_display(transition_trace_label, reset_button, undo_button)
    render_uml_diagram(
        canvas, svg_file_path, active_state=current_state, debug_mode=debug_mode
    )
    print("Transition trace reset.")


def undo_last_transition(transition_trace_label, reset_button, undo_button, canvas):
    global current_state, transition_trace, state_stack

    if transition_trace:
        previous_state = state_stack.pop() if state_stack else None

        if previous_state:
            current_state = previous_state
            transition_trace.pop()

            update_transition_display(transition_trace_label, reset_button, undo_button)

            render_uml_diagram(
                canvas, svg_file_path, active_state=current_state, debug_mode=debug_mode
            )

            undo_button["state"] = "normal"
        else:
            print("State stack is empty.")
            messagebox.showinfo("No Undo Available", "No further undo is possible.")
            undo_button["state"] = "disabled"
    else:
        print("No transitions to undo.")
        messagebox.showinfo("No Undo Available", "No further undo is possible.")
        undo_button["state"] = "disabled"
