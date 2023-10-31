import tempfile
import tkinter as tk
import xml.etree.ElementTree as ET
from tkinter import filedialog
from typing import Dict, List

import cairosvg
from PIL import Image, ImageTk

ELEMENTS = []
STATE_HIERARCHY: Dict[str, List[str]] = {}

debug_mode = False

svg_file_path = None


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


def build_state_hierarchy(elements):
    hierarchy = {}
    stack = []

    for state_name, (x1, x2, y1, y2) in elements:
        hierarchy[state_name] = []

        if stack:
            for parent_name, (px1, px2, py1, py2) in reversed(stack):
                if x1 >= px1 and x2 <= px2 and y1 >= py1 and y2 <= py2:
                    hierarchy[parent_name].append(state_name)
                    stack.append((state_name, (x1, x2, y1, y2)))
                    break
        else:
            stack.append((state_name, (x1, x2, y1, y2)))

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
    if not ELEMENTS:
        return

    x_offset = canvas.canvasx(0)
    y_offset = canvas.canvasy(0)

    x, y = event.x + x_offset, event.y + y_offset

    state_name = check_state(x, y)

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

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_png:
        temp_png.write(png_data)

    image = Image.open(temp_png.name)
    photo = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    canvas.image = photo

    if active_state:
        marked_states = find_active_states(active_state)
        for state, hierarchy in STATE_HIERARCHY.items():
            if state == active_state or state in marked_states:
                for element in ELEMENTS:
                    if element[0] == state:
                        x1, x2, y1, y2 = element[1]
                        outline_color = "red" if state != active_state else "green"
                        outline_width = 1 if state != active_state else 3
                        canvas.create_rectangle(x1, y1, x2, y2, outline=outline_color, width=outline_width)
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
    canvas.delete("all")
    ELEMENTS.clear()
    STATE_HIERARCHY.clear()
    parse_svg(file_path)
    max_x = max(state[1][1] for state in ELEMENTS)
    max_y = max(state[1][3] for state in ELEMENTS)
    canvas.config(width=max_x + 20, height=max_y + 20)
    svg_file_path = file_path
    render_uml_diagram(canvas, file_path, active_state=None)
    canvas.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))


def on_canvas_scroll(event):
    if event.delta > 0:
        canvas.yview_scroll(-1, "units")
    elif event.delta < 0:
        canvas.yview_scroll(1, "units")


app = tk.Tk()
app.title("UML Diagram Viewer")

button_frame = tk.Frame(app)
button_frame.pack(side=tk.TOP, fill=tk.X)

load_button = tk.Button(button_frame, text="Load UML Diagram", command=choose_file)
load_button.pack()

if debug_mode:
    toggle_button = tk.Button(button_frame, text="Toggle Color Mode", command=toggle_color_mode)
    toggle_button.pack()

state_name_entry = tk.Entry(button_frame)
state_name_entry.pack()
highlight_button = tk.Button(
    button_frame, text="Enter state name", command=lambda: Enter_state(state_name_entry.get())
)
highlight_button.pack()

canvas_frame = tk.Frame(app)
canvas_frame.pack(fill=tk.BOTH, expand=True)

canvas = tk.Canvas(canvas_frame, bg="white")
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

canvas.bind("<Button-1>", on_canvas_click)
canvas.bind("<MouseWheel>", on_canvas_scroll)

scrollbar = tk.Canvas(canvas_frame, width=10, bg="gray")
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

vsb = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
vsb.pack(side=tk.RIGHT, fill=tk.Y)
canvas.configure(yscrollcommand=vsb.set)

app.mainloop()
