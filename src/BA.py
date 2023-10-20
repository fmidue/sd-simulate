import tkinter as tk
from tkinter import filedialog
import cairosvg
from PIL import Image, ImageTk
import tempfile
import xml.etree.ElementTree as ET

ELEMENTS = []


def parse_svg(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    text_elements = root.findall(".//{http://www.w3.org/2000/svg}text")
    rect_elements = root.findall(".//{http://www.w3.org/2000/svg}rect")

    result_list = []

    state_hierarchy = {}

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

                for other_state, (ox1, ox2, oy1, oy2) in result_list:
                    if (x1 >= ox1 and x2 <= ox2 and y1 >= oy1 and y2 <= oy2) and (
                        state_name != other_state
                    ):
                        state_hierarchy[state_name] = other_state

    result_list.sort(key=lambda x: state_hierarchy.get(x[0], x[0]))

    global ELEMENTS
    ELEMENTS = result_list


def render_uml_diagram(canvas, svg_file_path):
    canvas.delete("all")

    if not svg_file_path:
        print("No SVG file selected.")
        return

    png_data = cairosvg.svg2png(url=svg_file_path)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_png:
        temp_png.write(png_data)

    image = Image.open(temp_png.name)
    photo = ImageTk.PhotoImage(image)

    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    canvas.image = photo


def on_canvas_click(event, root, canvas):
    x, y = event.x, event.y
    check_state(x, y, root, canvas)


def check_state(x, y, root, canvas):
    for element in reversed(ELEMENTS):
        x1, y1, x2, y2 = (
            element[1][0],
            element[1][2],
            element[1][1],
            element[1][3],
        )
        if x1 <= x <= x2 and y1 <= y <= y2:
            show_popup(element[0], x, y, root)
            break
    else:
        show_popup("Outside", x, y, root)


def show_popup(message, x, y, root):
    popup = tk.Toplevel(root)
    popup.title("Information")
    label_coords = tk.Label(popup, text=f"Clicked Coordinates (x, y): ({x}, {y})")
    label_state = tk.Label(popup, text=f"State: {message}")
    label_coords.pack()
    label_state.pack()
    popup.mainloop()


app = tk.Tk()
app.title("UML Diagram Viewer")

canvas = tk.Canvas(app, bg="white", width=600, height=600)
canvas.pack(expand=tk.YES, fill=tk.BOTH)
canvas.bind("<Button-1>", lambda event: on_canvas_click(event, app, canvas))


def choose_file():
    file_path = filedialog.askopenfilename(filetypes=[("SVG files", "*.svg")])

    if not file_path:
        return

    print("Selected File:", file_path)

    canvas.delete("all")
    ELEMENTS.clear()
    parse_svg(file_path)

    max_x = max(state[1][1] for state in ELEMENTS)
    max_y = max(state[1][3] for state in ELEMENTS)
    canvas.config(width=max_x + 20, height=max_y + 20)

    render_uml_diagram(canvas, file_path)


load_button = tk.Button(app, text="Load UML Diagram", command=choose_file)
load_button.pack()

app.mainloop()
