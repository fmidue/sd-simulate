import logging
import tkinter as tk
from tkinter import PhotoImage, messagebox

import cairosvg
import globals
from config import (
    DEFAULT_SCALE_FACTOR,
    HIGHLIGHT_COLOR_ACTIVE,
    HIGHLIGHT_COLOR_HINTS,
    HIGHLIGHT_COLOR_OUTLINE,
    HIGHLIGHT_COLOR_REMEMBERED,
    SWITCH_SIMULATION,
)
from state_manager import state_parameter
from svg_parser import (
    check_state_type1,
    check_state_type2,
    find_active_states,
    get_elements,
    get_hierarchy,
)
from utilities import parse_state, show_popup, state_representation


def render_uml_diagram(canvas):
    ELEMENTS = get_elements()
    STATE_HIERARCHY = get_hierarchy()

    if not globals.svg_file_path or not ELEMENTS:
        logging.error("No SVG file selected or no elements to display.")
        return

    modified_svg_content = globals.loaded_svg_content

    target_width = globals.original_width * globals.current_scale
    target_height = globals.original_height * globals.current_scale

    target_width = max(target_width, globals.MIN_WIDTH)
    target_height = max(target_height, globals.MIN_HEIGHT)

    def split_states(state_list):
        states = []
        for state in state_list:
            states.extend(state.split(","))
        return states

    if modified_svg_content:
        if ELEMENTS and (
            globals.current_scale * max(ELEMENTS, key=lambda item: item[1][1])[1][1]
            < globals.MIN_WIDTH
            or globals.current_scale * max(ELEMENTS, key=lambda item: item[1][3])[1][3]
            < globals.MIN_HEIGHT
        ):
            logging.error("SVG dimensions too small for rendering.")
            return

        if globals.is_svg_updated or globals.current_scale != globals.last_scale:
            png_data = cairosvg.svg2png(
                bytestring=globals.loaded_svg_content,
                output_width=target_width,
                output_height=target_height,
            )
            image = PhotoImage(data=png_data)
            globals.current_image = image

            canvas.delete("all")
            canvas.create_image(0, 0, anchor="nw", image=image)
            canvas.image = image

            globals.is_svg_updated = False
            globals.last_scale = globals.current_scale
        else:
            if globals.current_image is not None:
                canvas.delete("all")
                canvas.create_image(0, 0, anchor="nw", image=globals.current_image)
            else:
                logging.error("No current image to render.")

        if not ELEMENTS:
            logging.info("No elements to highlight. Only Rendering the SVG")
            return

        current = state_representation(globals.current_state)
        active_states, remembered_states = parse_state(current)

        for active_state in split_states(active_states):
            active_state = active_state.strip()
            marked_states = find_active_states(active_state)
            for state, hierarchy in STATE_HIERARCHY.items():
                if state == active_state or (
                    globals.show_parent_highlight and state in marked_states
                ):
                    for element in ELEMENTS:
                        if element[0] == state:
                            x1, x2, y1, y2 = [
                                int(coord * globals.current_scale)
                                for coord in element[1]
                            ]

                            outline_color = (
                                HIGHLIGHT_COLOR_ACTIVE
                                if state == active_state
                                else HIGHLIGHT_COLOR_OUTLINE
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

        for remembered_state in split_states(remembered_states):
            remembered_state = remembered_state.strip()
            for element in ELEMENTS:
                if element[0] == remembered_state:
                    x1, x2, y1, y2 = [
                        int(coord * globals.current_scale) for coord in element[1]
                    ]
                    canvas.create_rectangle(
                        x1, y1, x2, y2, outline=HIGHLIGHT_COLOR_REMEMBERED, width=2
                    )

        canvas.config(width=target_width, height=target_height)
        canvas.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))


def on_canvas_click(
    event, canvas, transition_trace_label, reset_button, undo_button, parent
):
    try:
        ELEMENTS = get_elements()
        state_hierarchy = get_hierarchy()

        if not ELEMENTS:
            return

        x_offset = canvas.canvasx(0)
        y_offset = canvas.canvasy(0)
        x = (event.x + x_offset) / globals.current_scale
        y = (event.y + y_offset) / globals.current_scale
        clicked_state = None

        if globals.xml_type == "Type1":
            clicked_state = check_state_type1(x, y)
        elif globals.xml_type == "Type2":
            state_hierarchy = check_state_type2(x, y)
            if state_hierarchy:
                clicked_state = state_hierarchy[-1]
        else:
            logging.error("Unknown XML type")
            return

        state_transitioned = state_parameter(
            clicked_state, transition_trace_label, reset_button, undo_button, parent
        )

        show_popup(clicked_state, x, y)
        if state_transitioned:
            render_uml_diagram(canvas)
        else:
            logging.info("No need to call render_uml_diagram")
    except Exception as e:
        logging.error("Error in on_canvas_click: %s", str(e))


def enter_state(
    state_name, canvas, transition_trace_label, reset_button, undo_button, parent
):
    state_transitioned = state_parameter(
        state_name, transition_trace_label, reset_button, undo_button, parent
    )

    if state_transitioned:
        render_uml_diagram(canvas)
    else:
        logging.info("No need to call render_uml_diagram")


def highlight_next_states(canvas, next_states):
    ELEMENTS = get_elements()

    current = state_representation(globals.current_state)
    active_current, _ = parse_state(current)

    split_current_states = set()
    for state in active_current:
        split_current_states.update(state.split(","))

    active_states = set()
    for state in next_states:
        active, _ = parse_state(state)
        for individual_state in active:
            active_states.update(individual_state.split(","))

    if len(split_current_states) > 1 and current not in next_states:
        active_states = active_states - split_current_states

    canvas.delete("hints")

    for state, coordinates in ELEMENTS:
        if state in active_states:
            x1, x2, y1, y2 = [
                int(coord * globals.current_scale) for coord in coordinates
            ]
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
                outline=HIGHLIGHT_COLOR_HINTS,
                width=2,
                tags="hints",
            )
    if globals.hints_visible:
        canvas.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))


def zoom(event, canvas):
    if event.state & 0x4:
        ELEMENTS = get_elements()
        scale_factor = DEFAULT_SCALE_FACTOR if event.delta > 0 else 0.9

        new_scale = globals.current_scale * scale_factor

        if (
            new_scale * max(ELEMENTS, key=lambda item: item[1][1])[1][1]
            < globals.MIN_WIDTH
            or new_scale * max(ELEMENTS, key=lambda item: item[1][3])[1][3]
            < globals.MIN_HEIGHT
        ):
            logging.error("Zoom limit reached.")
            return

        globals.current_scale = new_scale
        canvas.scale("all", event.x, event.y, scale_factor, scale_factor)

        scroll_x1, scroll_y1, scroll_x2, scroll_y2 = canvas.bbox("all")
        if (
            scroll_x1 is not None
            and scroll_y1 is not None
            and scroll_x2 is not None
            and scroll_y2 is not None
        ):
            canvas.config(scrollregion=(scroll_x1, scroll_y1, scroll_x2, scroll_y2))

        render_uml_diagram(canvas)
        if globals.hints_visible:
            current = state_representation(globals.current_state)
            next_states = globals.transitions.get(current, {}).keys()
            highlight_next_states(canvas, next_states)


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


def maximize_visible_canvas(canvas):
    ELEMENTS = get_elements()
    if not globals.svg_file_path or not ELEMENTS:
        return

    canvas.update_idletasks()
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()

    diagram_width = max(state[1][1] for state in ELEMENTS)
    diagram_height = max(state[1][3] for state in ELEMENTS)

    if diagram_width <= 0 or diagram_height <= 0:
        logging.error("Invalid diagram dimensions.")
        return

    width_zoom = max(canvas_width / diagram_width, 0.01)
    height_zoom = max(canvas_height / diagram_height, 0.01)

    proposed_scale = min(width_zoom*0.95, height_zoom*0.9)

    if (diagram_width * proposed_scale < globals.MIN_WIDTH) or (
        diagram_height * proposed_scale < globals.MIN_HEIGHT
    ):
        min_width_scale = globals.MIN_WIDTH / diagram_width
        min_height_scale = globals.MIN_HEIGHT / diagram_height
        globals.current_scale = max(min_width_scale*0.95, min_height_scale*0.9)
    else:
        globals.current_scale = proposed_scale

    render_uml_diagram(canvas)

    canvas.yview_moveto(0)
    canvas.xview_moveto(0)
    if globals.hints_visible:
        current = state_representation(globals.current_state)
        next_states = globals.transitions.get(current, {}).keys()
        highlight_next_states(canvas, next_states)


def clear_hints(canvas):
    canvas.delete("hints")


def toggle_mode(
    canvas,
    mode_switch,
    highlight_button,
    state_name_entry,
    button_show_graph,
    hint_button,
    reset_button,
    undo_button,
    reachability_button,
    analyze_button2,
    analyze_button3,
):
    globals.analysis_mode = not globals.analysis_mode
    if globals.analysis_mode:
        mode_switch.config(text=SWITCH_SIMULATION)
        state_name_entry.pack_forget()
        highlight_button.pack_forget()
        hint_button.pack_forget()
        reset_button.pack_forget()
        undo_button.pack_forget()
        button_show_graph.pack_forget()

        analyze_button3.pack(side=tk.LEFT, padx=(5, 5))
        analyze_button2.pack(side=tk.LEFT, padx=(5, 5))
        reachability_button.pack(side=tk.LEFT, padx=(5, 5))

    else:
        mode_switch.config(text="Switch to Analysis Mode")
        state_name_entry.pack(side=tk.LEFT, padx=(0, 5))
        highlight_button.pack(side=tk.LEFT, padx=(0, 5))
        hint_button.pack(side=tk.LEFT, padx=(5, 5))
        reset_button.pack(side=tk.LEFT, padx=(5, 5))
        undo_button.pack(side=tk.LEFT, padx=(5, 5))
        button_show_graph.pack(side=tk.LEFT, padx=(0, 25))

        analyze_button3.pack_forget()
        analyze_button2.pack_forget()
        reachability_button.pack_forget()

    canvas.update_idletasks()


def show_hints(canvas):
    current_state_hints = state_representation(globals.current_state)
    next_states = globals.transitions.get(current_state_hints, {}).keys()

    clear_hints(canvas)

    if next_states and not globals.hints_visible:
        highlight_next_states(canvas, next_states)
        globals.hints_visible = True
    elif not next_states:
        messagebox.showinfo("No More Steps", "No more further steps are possible.")
        globals.hints_visible = False
    elif globals.hints_visible:
        clear_hints(canvas)
        globals.hints_visible = False
