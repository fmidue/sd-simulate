import tkinter as tk
from tkinter import filedialog
import cairosvg
from PIL import Image, ImageTk
import tempfile
import xml.etree.ElementTree as ET

ELEMENTS = []
STATE_HIERARCHY = {}

color_mode = True

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
    global color_mode, svg_file_path
    color_mode = not color_mode
    if svg_file_path:
        render_uml_diagram(canvas, svg_file_path)


def on_canvas_click(event):
    if not ELEMENTS:
        return
    x, y = event.x, event.y
    state_name = check_state(x, y)
    show_popup(state_name, x, y)


def check_state(x, y):
    for element in reversed(ELEMENTS):
        x1, y1, x2, y2 = (
            element[1][0],
            element[1][2],
            element[1][1],
            element[1][3],
        )
        if x1 <= x <= x2 and y1 <= y <= y2:
            return element[0]
    return "Outside"


def show_popup(message, x, y):
    popup = tk.Toplevel()
    popup.title("Information")
    label_coords = tk.Label(popup, text=f"Clicked Coordinates (x, y): ({x}, {y})")
    label_state = tk.Label(popup, text=f"State: {message}")
    label_coords.pack()
    label_state.pack()


def render_uml_diagram(canvas, svg_file_path):
    canvas.delete("all")
    if not svg_file_path:
        print("No SVG file selected.")
        return
    with open(svg_file_path, "r") as svg_file:
        svg_content = svg_file.read()
    if color_mode:
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
    render_uml_diagram(canvas, file_path)


app = tk.Tk()
app.title("UML Diagram Viewer")

canvas = tk.Canvas(app, bg="white", width=600, height=600)
canvas.pack(expand=tk.YES, fill=tk.BOTH)

load_button = tk.Button(app, text="Load UML Diagram", command=choose_file)
load_button.pack()

toggle_button = tk.Button(
    app, text="Switch Color Mode", command=toggle_color_mode
)
toggle_button.pack()

canvas.bind("<Button-1>", on_canvas_click)

app.mainloop()
