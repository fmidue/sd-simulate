import os
import tkinter as tk
import xml.etree.ElementTree as ET
from io import BytesIO
from tkinter import PhotoImage, filedialog

import cairosvg
from PIL import Image
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

ACTIVE_STATE = None
current_scale = 1.0
debug_mode = False
xml_type = None
loaded_svg_content = None
MIN_WIDTH = 1
MIN_HEIGHT = 1


def on_canvas_click(event, canvas):
    global ACTIVE_STATE, current_scale
    ELEMENTS = get_elements()
    if not ELEMENTS:
        return

    x_offset = canvas.canvasx(0)
    y_offset = canvas.canvasy(0)

    x = (event.x + x_offset) / current_scale
    y = (event.y + y_offset) / current_scale

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
    render_uml_diagram(
        canvas, svg_file_path, active_state=ACTIVE_STATE, debug_mode=debug_mode
    )


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


def render_uml_diagram(canvas, svg_file_path, active_state, debug_mode):
    global loaded_svg_content
    print("Rendering UML diagram using existing content.")
    ELEMENTS = get_elements()
    STATE_HIERARCHY = get_hierarchy()
    canvas.delete("all")
    if not svg_file_path:
        print("No SVG file selected.")
        return

    modified_svg_content = loaded_svg_content

    if modified_svg_content:
        if (
            current_scale * max(ELEMENTS, key=lambda item: item[1][1])[1][1] < MIN_WIDTH
            or current_scale * max(ELEMENTS, key=lambda item: item[1][3])[1][3]
            < MIN_HEIGHT
        ):
            print("SVG dimensions too small for rendering.")
            return
        png_data = cairosvg.svg2png(
            bytestring=modified_svg_content, scale=current_scale
        )
        image = PhotoImage(data=png_data)

        png_image = Image.open(BytesIO(png_data))

        new_width = max(int(png_image.width * current_scale), MIN_WIDTH)
        new_height = max(int(png_image.height * current_scale), MIN_HEIGHT)

        print(f"Resizing to Width: {new_width}, Height: {new_height}")

        if new_width <= 0 or new_height <= 0:
            print("Invalid image dimensions for resize.")
            return

        png_image = png_image.resize((new_width, new_height))

        canvas.delete("all")
        canvas.create_image(0, 0, anchor="nw", image=image)
        canvas.image = image

        if not ELEMENTS:
            print("No elements to highlight. Only Rendering the SVG")
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
                                x1,
                                y1,
                                x2,
                                y2,
                                outline=outline_color,
                                width=outline_width,
                            )
                            break

        max_x = max(ELEMENTS, key=lambda item: item[1][1])[1][1]
        max_y = max(ELEMENTS, key=lambda item: item[1][3])[1][3]
        canvas.config(width=max_x + 20, height=max_y + 20)


def Enter_state(state_name, canvas):
    render_uml_diagram(
        canvas, svg_file_path, active_state=state_name, debug_mode=debug_mode
    )


def choose_file(canvas):
    global svg_file_path, xml_type, svg_rainbow_file_path, loaded_svg_content
    ELEMENTS = get_elements()
    STATE_HIERARCHY = get_hierarchy()

    file_path = filedialog.askopenfilename(filetypes=[("SVG files", "*.svg")])
    if not file_path:
        return
    print("Selected File:", file_path)

    if file_path.endswith("_rainbow.svg"):
        svg_rainbow_file_path = file_path
        svg_file_path = file_path.replace("_rainbow.svg", ".svg")
    else:
        svg_file_path = file_path
        svg_rainbow_file_path = file_path.replace(".svg", "_rainbow.svg")

    if not os.path.isfile(svg_file_path) or not os.path.isfile(svg_rainbow_file_path):
        print("You don't have both file types needed.")
        return

    loaded_svg_content = get_modified_svg_content()
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

    if ELEMENTS:
        max_x = max(state[1][1] for state in ELEMENTS)
        max_y = max(state[1][3] for state in ELEMENTS)
        canvas.config(width=max_x + 20, height=max_y + 20)

    render_uml_diagram(canvas, svg_file_path, active_state=None, debug_mode=debug_mode)
    canvas.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))


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
            canvas, svg_file_path, active_state=ACTIVE_STATE, debug_mode=debug_mode
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
        canvas, svg_file_path, active_state=ACTIVE_STATE, debug_mode=debug_mode
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
