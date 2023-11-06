import re
import tkinter as tk
import xml.etree.ElementTree as ET
from io import BytesIO
from tkinter import filedialog
from typing import Dict, List

import cairosvg
from PIL import Image, ImageTk

ELEMENTS = []
STATE_HIERARCHY: Dict[str, List[str]] = {}
debug_mode = False
svg_file_path = None
ACTIVE_STATE = None
current_scale = 1.0
canvas = None


def identify_xml_type(root):
    g_elements = root.findall(".//{http://www.w3.org/2000/svg}g")
    has_id = any(g.get("id") is not None for g in g_elements)
    if has_id:
        return "Type1"
    else:
        return "Type2"


def parse_svg(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    result_list = []
    text_elements = root.findall(".//{http://www.w3.org/2000/svg}text")
    rect_elements = root.findall(".//{http://www.w3.org/2000/svg}rect")

    for text_element in text_elements:
        text_fill_color = text_element.get("fill")
        if text_fill_color != "#000000":
            matching_rect = None
            for rect_element in rect_elements:
                rect_stroke_match = rect_element.get("style")
                if f"stroke:{text_fill_color};" in rect_stroke_match:
                    matching_rect = rect_element
                    break
            if matching_rect is not None:
                state_name = text_element.text.strip()
                rect_x = float(matching_rect.get("x"))
                rect_y = float(matching_rect.get("y"))
                rect_width = float(matching_rect.get("width"))
                rect_height = float(matching_rect.get("height"))
                x1 = rect_x
                x2 = rect_x + rect_width
                y1 = rect_y
                y2 = rect_y + rect_height
                result_list.append((state_name, (x1, x2, y1, y2)))

    result_list.sort(key=lambda x: (len(STATE_HIERARCHY.get(x[0], [])), x[1][0]))
    STATE_HIERARCHY.update(build_state_hierarchy(result_list))

    for state, hierarchy in STATE_HIERARCHY.items():
        print(f"State: {state}")
        print(f"Children: {hierarchy}")
        print()

    global ELEMENTS
    ELEMENTS = result_list


def svg_path_to_coords(path_str):
    x_values = []
    y_values = []

    commands = re.findall(
        r"([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)", path_str
    )

    current_x, current_y = 0, 0

    for command, data_str in commands:
        data = list(map(float, re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", data_str)))

        if command in "M":
            current_x, current_y = data[0], data[1]
            x_values.append(current_x)
            y_values.append(current_y)

        elif command in "h":
            for x in data:
                current_x = current_x + x
                x_values.append(current_x)

        elif command in "v":
            for y in data:
                current_y = current_y + y
                y_values.append(current_y)

        elif command in "c":
            current_x = current_x + data[4]
            current_y = current_y + data[5]
            x_values.append(current_x)
            y_values.append(current_y)

    if x_values and y_values:
        x1 = min(x_values)
        x2 = max(x_values)
        y1 = min(y_values)
        y2 = max(y_values)

        return x1, x2, y1, y2

    return None


def parse_svg2(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    result_list = []

    group_elements = root.findall(".//{http://www.w3.org/2000/svg}g")

    for group_element in group_elements:
        group_fill_color = group_element.get("fill")
        print(f"Group Fill Color: {group_fill_color}")
        if group_fill_color == "rgb(0,0,0)":
            print("here skipped black colored group")
            continue

        text_element = group_element.find(".//{http://www.w3.org/2000/svg}text")

        if text_element is not None:
            if text_element.text:
                state_name = text_element.text.strip()
            else:
                state_name = "''"
            print(f"Found Text Element: {state_name}")
        else:
            print("No Text Element found in group")
            continue

        related_path = None
        for path_element in root.findall(".//{http://www.w3.org/2000/svg}g"):
            path_stroke_color = path_element.get("stroke")

            if path_stroke_color is not None:
                path = path_element.find(".//{http://www.w3.org/2000/svg}path")
                print(f"Path Stroke Color: {path_stroke_color}")
                if path_stroke_color == group_fill_color:
                    related_path = path.get("d")
                    break

        if related_path:
            coordinates = svg_path_to_coords(related_path)
            if coordinates:
                result_list.append((state_name, coordinates))
            print(f"Added State: {state_name}")
            print(f"Related Path: {related_path}")
        else:
            print(f"No matching path found for state: {state_name}")

    for state, coordinates in result_list:
        print(f"State: {state}")
        print(f"Coordinates: {coordinates}")
        print()

    global STATE_HIERARCHY
    STATE_HIERARCHY = build_state_hierarchy(result_list)

    if result_list:
        max_x = max(coordinates[1] for _, coordinates in result_list)
        max_y = max(coordinates[3] for _, coordinates in result_list)
        print(f"Max X: {max_x}")
        print(f"Max Y: {max_y}")
    else:
        print("The selected SVG doesn't contain the expected elements.")

    for state, hierarchy in STATE_HIERARCHY.items():
        print(f"State: {state}")
        print(f"Children: {hierarchy}")
        print()

    global ELEMENTS
    ELEMENTS = result_list


def build_state_hierarchy(states):
    hierarchy = {state: [] for state, _ in states}

    states = sorted(states, key=lambda x: (x[1][1] - x[1][0]) * (x[1][3] - x[1][2]))

    for i, (child_state, child_coords) in enumerate(states):
        for j in range(i + 1, len(states)):
            parent_state, parent_coords = states[j]
            if (
                parent_coords[0] <= child_coords[0]
                and parent_coords[1] >= child_coords[1]
                and parent_coords[2] <= child_coords[2]
                and parent_coords[3] >= child_coords[3]
            ):
                hierarchy[parent_state].append(child_state)
                break

    return hierarchy


def no_colors_diagram(svg_content):
    root = ET.fromstring(svg_content)
    text_elements = root.findall(".//{http://www.w3.org/2000/svg}text")
    rect_elements = root.findall(".//{http://www.w3.org/2000/svg}rect")
    line_elements = root.findall(".//{http://www.w3.org/2000/svg}line")

    for text_element in text_elements:
        text_element.set("fill", "#000000")
    for element in rect_elements + line_elements:
        style = element.get("style")
        style = style.replace("stroke:#", "stroke:#000000;")
        element.set("style", style)

    modified_svg_content = ET.tostring(root, encoding="unicode")
    return modified_svg_content


def toggle_color_mode():
    global debug_mode
    debug_mode = not debug_mode
    if svg_file_path:
        render_uml_diagram(canvas, svg_file_path, active_state=None)


def on_canvas_click(event):
    global ACTIVE_STATE, current_scale

    if not ELEMENTS:
        return

    x_offset = canvas.canvasx(0)
    y_offset = canvas.canvasy(0)

    x = (event.x + x_offset) / current_scale
    y = (event.y + y_offset) / current_scale

    xml_type = identify_xml_type(ET.parse(svg_file_path).getroot())

    if xml_type == "Type1":
        state_name = check_state_type1(x, y)
    else:
        state_hierarchy = check_state_type2(x, y)
        if state_hierarchy:
            state_name = state_hierarchy[-1]

    show_popup(state_name, x, y)
    ACTIVE_STATE = state_name

    print(f"Clicked state: {state_name}")
    marked_states = find_active_states(state_name)
    print(f"Marked states: {marked_states}")
    render_uml_diagram(canvas, svg_file_path, active_state=ACTIVE_STATE)


def check_state(x, y):
    for element in reversed(ELEMENTS):
        x1, x2, y1, y2 = element[1]
        if x1 <= x <= x2 and y1 <= y <= y2:
            return element[0]
    return "Outside"


def check_state_type1(x, y):
    print(f"Checking state for x={x}, y={y}")

    for element in reversed(ELEMENTS):
        x1, x2, y1, y2 = element[1]
        print(f"Checking against x1={x1}, x2={x2}, y1={y1}, y2={y2}")
        if x1 <= x <= x2 and y1 <= y <= y2:
            print(f"Matched with {element[0]}")
            return element[0]
    print("Outside")
    return "Outside"


def check_state_type2(x, y, state=None, state_hierarchy=None):
    if state is None:
        state = "Outside"
    if state_hierarchy is None:
        state_hierarchy = []

    for element in ELEMENTS:
        x1, x2, y1, y2 = element[1]
        if x1 <= x <= x2 and y1 <= y <= y2:
            state = element[0]
            break

    if state not in state_hierarchy:
        state_hierarchy.append(state)
        parent_states = STATE_HIERARCHY.get(state, [])
        for parent_state in parent_states:
            check_state_type2(x, y, parent_state, state_hierarchy)

    return state_hierarchy


def show_popup(message, x, y):
    if debug_mode:
        popup = tk.Toplevel()
        popup.title("Information")
        label_coords = tk.Label(popup, text=f"Clicked Coordinates (x, y): ({x}, {y})")
        label_state = tk.Label(popup, text=f"State: {message}")
        label_coords.pack()
        label_state.pack()


def render_uml_diagram(canvas, svg_file_path, active_state):
    canvas.delete("all")
    if not svg_file_path:
        print("No SVG file selected.")
        return

    with open(svg_file_path, "r") as svg_file:
        svg_content = svg_file.read()

    if debug_mode:
        modified_svg_content = svg_content
    else:
        modified_svg_content = no_colors_diagram(svg_content)

    png_data = cairosvg.svg2png(bytestring=modified_svg_content)

    png_image = Image.open(BytesIO(png_data))

    png_image = png_image.resize(
        (int(png_image.width * current_scale), int(png_image.height * current_scale))
    )

    photo = ImageTk.PhotoImage(png_image)
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    canvas.image = photo

    if not ELEMENTS:
        print("No elements to highlight.Only Rendering the SVG ")
        return

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
                            x1, y1, x2, y2, outline=outline_color, width=outline_width
                        )
                        break

    max_x = max(ELEMENTS, key=lambda item: item[1][1])[1][1]
    max_y = max(ELEMENTS, key=lambda item: item[1][3])[1][3]
    canvas.config(width=max_x + 20, height=max_y + 20)


def find_active_states(state):
    marked_states = {state}
    for parent_state, child_states in STATE_HIERARCHY.items():
        if state in child_states:
            marked_states.add(parent_state)
            print(f"Marked state: {parent_state}")
            marked_states.update(find_active_states(parent_state))
    return marked_states


def Enter_state(state_name):
    render_uml_diagram(canvas, svg_file_path, active_state=state_name)


def choose_file():
    global svg_file_path
    file_path = filedialog.askopenfilename(filetypes=[("SVG files", "*.svg")])
    if not file_path:
        return
    print("Selected File:", file_path)

    tree = ET.parse(file_path)
    root = tree.getroot()
    xml_type = identify_xml_type(root)

    if xml_type == "Type1":
        print("Handling Type 1 XML.")
        canvas.delete("all")
        ELEMENTS.clear()
        STATE_HIERARCHY.clear()
        parse_svg(file_path)
    elif xml_type == "Type2":
        print("Handling Type 2 XML.")
        canvas.delete("all")
        ELEMENTS.clear()
        STATE_HIERARCHY.clear()
        parse_svg2(file_path)
    else:
        print("Unknown file type")

    if ELEMENTS:
        max_x = max(state[1][1] for state in ELEMENTS)
        max_y = max(state[1][3] for state in ELEMENTS)
        canvas.config(width=max_x + 20, height=max_y + 20)

    svg_file_path = file_path
    render_uml_diagram(canvas, file_path, active_state=None)
    canvas.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))


def on_canvas_scroll(event):
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


def zoom(event):
    global current_scale
    scale_factor = 1.1 if event.delta > 0 else 0.9
    current_scale *= scale_factor

    x = canvas.canvasx(event.x)
    y = canvas.canvasy(event.y)
    canvas.scale("all", x, y, scale_factor, scale_factor)

    scroll_x1, scroll_y1, scroll_x2, scroll_y2 = canvas.bbox("all")
    canvas.config(scrollregion=(scroll_x1, scroll_y1, scroll_x2, scroll_y2))

    render_uml_diagram(canvas, svg_file_path, active_state=ACTIVE_STATE)


def maximize_visible_canvas():
    global current_scale, canvas
    if not svg_file_path or not ELEMENTS:
        return

    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()

    diagram_width = max(state[1][1] for state in ELEMENTS)
    diagram_height = max(state[1][3] for state in ELEMENTS)

    if canvas_width < 1 or canvas_height < 1 or diagram_width < 1 or diagram_height < 1:
        return

    width_zoom = canvas_width / diagram_width
    height_zoom = canvas_height / diagram_height

    current_scale = min(width_zoom, height_zoom)

    render_uml_diagram(canvas, svg_file_path, active_state=ACTIVE_STATE)


app = tk.Tk()
app.title("UML Diagram Viewer")

button_frame = tk.Frame(app)
button_frame.pack(side=tk.TOP, fill=tk.X)

load_button = tk.Button(button_frame, text="Load UML Diagram", command=choose_file)
load_button.pack()

maximize_zoom_button = tk.Button(
    button_frame, text="Maximize Zoom", command=maximize_visible_canvas
)
maximize_zoom_button.pack()

if debug_mode:
    toggle_button = tk.Button(
        button_frame, text="Toggle Color Mode", command=toggle_color_mode
    )
    toggle_button.pack()

state_name_entry = tk.Entry(button_frame)
state_name_entry.pack()
highlight_button = tk.Button(
    button_frame,
    text="Enter state name",
    command=lambda: Enter_state(state_name_entry.get()),
)
highlight_button.pack()


canvas_frame = tk.Frame(app)
canvas_frame.pack(fill=tk.BOTH, expand=True)

canvas = tk.Canvas(canvas_frame, bg="white")
canvas.grid(row=0, column=0, sticky="nsew")

vertical_scroll_bar = tk.Scrollbar(
    canvas_frame, orient=tk.VERTICAL, command=canvas.yview, bg="gray"
)
vertical_scroll_bar.grid(row=0, column=1, sticky="ns")
canvas.configure(yscrollcommand=vertical_scroll_bar.set)

horizontal_scroll_bar = tk.Scrollbar(
    canvas_frame, orient=tk.HORIZONTAL, command=canvas.xview, bg="gray"
)
horizontal_scroll_bar.grid(row=1, column=0, sticky="ew")
canvas.configure(xscrollcommand=horizontal_scroll_bar.set)

canvas_frame.grid_rowconfigure(0, weight=1)
canvas_frame.grid_columnconfigure(0, weight=1)

canvas.bind("<Control-MouseWheel>", zoom)
canvas.bind("<Control-Button-4>", zoom)
canvas.bind("<Control-Button-5>", zoom)
canvas.bind("<Command-MouseWheel>", zoom)


canvas.bind("<MouseWheel>", on_canvas_scroll)
canvas.bind("<Button-1>", on_canvas_click)


app.mainloop()
