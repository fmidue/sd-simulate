import tkinter as tk
from tkinter import filedialog
import xml.etree.ElementTree as ET
import cairosvg
from PIL import Image, ImageTk
import tempfile

ELEMENTS = []


def parse_svg(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    groups = root.findall(".//{http://www.w3.org/2000/svg}g")

    for group in groups:
        rect_element = group.find(".//{http://www.w3.org/2000/svg}rect")
        text_element = group.find(".//{http://www.w3.org/2000/svg}text")

        if rect_element is not None and text_element is not None:
            x = float(rect_element.get("x"))
            y = float(rect_element.get("y"))
            width = float(rect_element.get("width"))
            height = float(rect_element.get("height"))
            state_name = text_element.text

            ELEMENTS.append(
                {
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "name": state_name,
                }
            )


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
            element["x"],
            element["y"],
            element["x"] + element["width"],
            element["y"] + element["height"],
        )
        if x1 <= x <= x2 and y1 <= y <= y2:
            show_popup(element["name"], x, y, root)
            break
    else:
        show_popup("Outside", x, y, root)


def show_popup(message, x, y, root):
    popup = tk.Toplevel(root)
    popup.title("Information")
    label_coords = tk.Label(
        popup, text=f"Clicked Coordinates (x, y): ({x}, {y})"
    )
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

    max_x = max(state["x"] + state["width"] for state in ELEMENTS)
    max_y = max(state["y"] + state["height"] for state in ELEMENTS)
    canvas.config(width=max_x + 20, height=max_y + 20)

    render_uml_diagram(canvas, file_path)


load_button = tk.Button(app, text="Load UML Diagram", command=choose_file)
load_button.pack()

app.mainloop()
