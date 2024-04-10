import os
import xml.etree.ElementTree as ET
from tkinter import filedialog, messagebox

import globals
import logging
from canvas_operations import clear_hints, render_uml_diagram
from config import FILE_TYPES
from state_manager import read_transitions_from_file
from svg_parser import (
    get_elements,
    get_hierarchy,
    identify_xml_type,
    parse_svg,
    parse_svg2,
)
from utilities import get_svg_dimensions, update_transition_display


def choose_file(canvas, transition_trace_label, reset_button, undo_button):
    ELEMENTS = get_elements()
    STATE_HIERARCHY = get_hierarchy()

    file_path = filedialog.askopenfilename(filetypes=FILE_TYPES)
    if not file_path:
        return False

    _, extension = os.path.splitext(file_path)

    if extension == ".svg":
        globals.svg_file_path = file_path
        if "_rainbow.svg" in globals.svg_file_path:
            globals.svg_rainbow_file_path = globals.svg_file_path
            globals.svg_file_path = globals.svg_rainbow_file_path.replace(
                "_rainbow.svg", ".svg"
            )
        else:
            globals.svg_rainbow_file_path = globals.svg_file_path.replace(
                ".svg", "_rainbow.svg"
            )
        globals.transitions_file_path = globals.svg_file_path.replace(
            ".svg", "_flattened.txt"
        )
    elif extension == ".txt":
        globals.transitions_file_path = file_path
        globals.svg_rainbow_file_path = globals.transitions_file_path.replace(
            "_flattened.txt", "_rainbow.svg"
        )
        globals.svg_file_path = globals.svg_rainbow_file_path.replace(
            "_rainbow.svg", ".svg"
        )
    else:
        messagebox.showinfo(
                "Invalid File Type",
                f"No SVG file selected or no elements to display.",
            )
        logging.error("Unsupported file type selected.")
        return False

    if (
        not os.path.isfile(globals.svg_file_path)
        or not os.path.isfile(globals.svg_rainbow_file_path)
        or not os.path.isfile(globals.transitions_file_path)
    ):
        messagebox.showinfo(
                "Missing File Type",
                f"You don't have all file types needed",
            )
        logging.error("User selection missing File Type(s)")
        return False

    globals.transitions_file_path = globals.transitions_file_path

    globals.loaded_svg_content = get_modified_svg_content()
    if globals.loaded_svg_content:
        globals.current_state = {"active": None, "remembered": None}
        globals.transition_trace.clear()
        globals.state_stack.clear()
        update_transition_display(transition_trace_label, reset_button, undo_button)
        clear_hints(canvas)
        globals.hints_visible = False
        globals.is_svg_updated = True
        globals.original_width, globals.original_height = get_svg_dimensions(
            globals.loaded_svg_content
        )
    tree = ET.parse(globals.svg_rainbow_file_path)
    root = tree.getroot()
    globals.xml_type = identify_xml_type(root)

    if globals.xml_type == "Type1":
        canvas.delete("all")
        ELEMENTS, STATE_HIERARCHY = parse_svg(globals.svg_rainbow_file_path)
    elif globals.xml_type == "Type2":
        canvas.delete("all")
        ELEMENTS, STATE_HIERARCHY = parse_svg2(globals.svg_rainbow_file_path)
    else:
        logging.error("Unknown file type")
        return False

    globals.current_state, globals.transitions = read_transitions_from_file(
        globals.transitions_file_path
    )

    if ELEMENTS:
        max_x = max(state[1][1] for state in ELEMENTS)
        max_y = max(state[1][3] for state in ELEMENTS)
        canvas.config(width=max_x + 20, height=max_y + 20)

    render_uml_diagram(canvas)
    canvas.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))
    return True


def get_modified_svg_content():
    if globals.debug_mode:
        selected_svg_file = globals.svg_rainbow_file_path
    else:
        selected_svg_file = globals.svg_file_path

    if selected_svg_file and os.path.exists(selected_svg_file):
        with open(selected_svg_file, "r") as svg_file:
            return svg_file.read()
    else:
        return None


def toggle_color_mode(canvas):
    globals.loaded_svg_content = get_modified_svg_content()

    if globals.loaded_svg_content:
        render_uml_diagram(canvas)


def reset_trace(transition_trace_label, reset_button, undo_button, canvas):
    if globals.state_stack:
        globals.current_state = globals.state_stack[0].copy()
    else:
        globals.current_state = {"active": None, "remembered": None}

    globals.state_stack.clear()

    globals.transition_trace = []

    clear_hints(canvas)
    globals.hints_visible = False

    update_transition_display(transition_trace_label, reset_button, undo_button)
    render_uml_diagram(canvas)

def undo_last_transition(transition_trace_label, reset_button, undo_button, canvas):
    if globals.transition_trace:
        if globals.state_stack:
            previous_state = globals.state_stack.pop()
            globals.current_state = previous_state.copy()
        else:
            globals.current_state = {"active": None, "remembered": None}

        if previous_state:
            globals.transition_trace.pop()

            update_transition_display(transition_trace_label, reset_button, undo_button)

            render_uml_diagram(canvas)

            undo_button["state"] = "normal"
            clear_hints(canvas)
            globals.hints_visible = False
        else:
            messagebox.showinfo("No Undo Available", "No further undo is possible.")
            undo_button["state"] = "disabled"
    else:
        logging.error("No transitions to undo.")
        messagebox.showinfo("No Undo Available", "No further undo is possible.")
        undo_button["state"] = "disabled"
