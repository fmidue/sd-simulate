import argparse
import logging
import tkinter as tk
from tkinter import Button, Canvas, Checkbutton, Entry, IntVar, Scrollbar, messagebox

import globals
from canvas_operations import (
    enter_state,
    maximize_visible_canvas,
    on_canvas_click,
    on_canvas_scroll,
    render_uml_diagram,
    show_hints,
    zoom,
)
from config import (
    APP_EXIT_MESSAGE,
    APP_TITLE,
    CANVAS_BG,
    DEFAULT_WINDOW_SIZE,
    LABEL_FONT,
    SCROLLBAR_BG,
    TITLE_FONT,
    TRANSITION_TRACE_BG,
    TRANSITION_TRACE_FG,
    TRANSITION_TRACE_TITLE_BG,
)
from graph_analysis import (
    decide_graph_analysis,
    on_reachability_analysis,
    perform_reachability_analysis,
)
from graph_visualization import show_state_diagram_graph
from GUI import (
    choose_file,
    reset_trace,
    undo_last_transition,
    update_transition_display,
)

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", action="store_true", default=False)
args = parser.parse_args()
globals.debug_mode |= args.debug

logging.basicConfig(
    filename="app.log", level="DEBUG", format="%(levelname)s:%(message)s"
)

highlight_button = None
reset_button = None
undo_button = None
hint_button = None

reachability_button = None
max_nodes_path = None
max_transition_path = None


def run_app():
    global app, transition_trace_label
    app = tk.Tk()
    app.title(APP_TITLE)
    app.geometry(DEFAULT_WINDOW_SIZE)

    trace_frame = tk.Frame(app)
    trace_frame.pack(side=tk.BOTTOM, fill=tk.X)

    right_trace_frame: tk.Frame = tk.Frame(trace_frame)
    right_trace_frame.pack(side=tk.RIGHT)

    transition_trace_frame = tk.Frame(app)
    transition_trace_frame.pack(side=tk.BOTTOM, fill=tk.X)

    left_transition_trace_frame: tk.Frame = tk.Frame(transition_trace_frame)
    left_transition_trace_frame.pack(side=tk.LEFT)

    transition_trace_container = tk.Frame(left_transition_trace_frame)
    transition_trace_container.pack(fill=tk.BOTH, expand=True)

    def on_file_loaded():
        global current_transitions, initial_state_key
        if choose_file(canvas, transition_trace_label, reset_button, undo_button):
            highlight_button["state"] = "normal"
            maximize_zoom_button["state"] = "normal"
            hint_button["state"] = "normal"
            reset_button["state"] = "disabled"
            undo_button["state"] = "disabled"
            button_show_graph["state"] = "normal"
            reachability_button["state"] = "normal"
            max_nodes_path["state"] = "normal"
            max_transition_path["state"] = "normal"

            current_transitions = globals.transitions
            initial_state_key = globals.initial_state_key
            globals.analysis_results_text.pack_forget()
            globals.analysis_results_visible = False
            perform_reachability_analysis(current_transitions, initial_state_key)

    def update_text_width():
        canvas_width = canvas.winfo_width()
        chars_per_pixel = 0.13
        text_width_in_chars = int(canvas_width * chars_per_pixel)
        transition_trace_label.config(width=text_width_in_chars)

    show_parent_highlight_var = IntVar(value=1)
    show_parent_highlight_checkbox = Checkbutton(
        right_trace_frame,
        text="Show Containment",
        variable=show_parent_highlight_var,
        command=lambda: [
            setattr(
                globals, "show_parent_highlight", bool(show_parent_highlight_var.get())
            ),
            render_uml_diagram(canvas),
        ],
    )
    show_parent_highlight_checkbox.pack(side=tk.LEFT, padx=(0, 10))

    hint_button = tk.Button(
        right_trace_frame,
        text="Hint",
        state="disabled",
        command=lambda: show_hints(canvas),
    )
    hint_button.pack(side=tk.LEFT, padx=(5, 5))

    reset_button: Button = tk.Button(
        right_trace_frame,
        text="Reset Trace",
        state="disabled",
        command=lambda: reset_trace(
            transition_trace_label, reset_button, undo_button, canvas
        ),
    )
    reset_button.pack(side=tk.LEFT, padx=(5, 5))

    undo_button: tk.Button = tk.Button(
        right_trace_frame,
        text="Undo",
        command=lambda: undo_last_transition(
            transition_trace_label, reset_button, undo_button, canvas
        ),
    )
    undo_button.pack(side=tk.LEFT, padx=(5, 5))

    button_frame = tk.Frame(app)
    button_frame.pack(side=tk.TOP, fill=tk.X)

    left_button_frame: tk.Frame = tk.Frame(button_frame)
    left_button_frame.pack(side=tk.LEFT)

    right_button_frame: tk.Frame = tk.Frame(button_frame)
    right_button_frame.pack(side=tk.RIGHT)

    load_button: Button = tk.Button(
        left_button_frame, text="Load UML Diagram", command=on_file_loaded
    )

    canvas_frame: tk.Frame = tk.Frame(app)
    canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    globals.analysis_results_text = tk.Text(app, height=25, width=50)
    globals.analysis_results_text.pack(side=tk.RIGHT, fill=tk.Y)
    globals.analysis_results_text.config(state=tk.DISABLED)
    globals.analysis_results_text.pack_forget()

    def show_analysis_results(title, content):
        new_content = f"{title}\n\n{content}"
        globals.analysis_results_text.config(state=tk.NORMAL)
        globals.analysis_results_text.delete("1.0", tk.END)
        globals.analysis_results_text.insert(tk.END, new_content)
        globals.analysis_results_text.config(state=tk.DISABLED)
        if not globals.analysis_results_visible:
            globals.analysis_results_text.pack(side=tk.RIGHT, fill=tk.Y)
            globals.analysis_results_visible = True
        else:
            if new_content == globals.full_content:
                globals.analysis_results_text.pack_forget()
                globals.analysis_results_visible = False
        globals.full_content = new_content

    canvas: Canvas = tk.Canvas(canvas_frame, bg=CANVAS_BG)
    canvas.grid(row=0, column=0, sticky="nsew")

    maximize_zoom_button: Button = tk.Button(
        right_button_frame,
        text="Full View",
        state="disabled",
        command=lambda: maximize_visible_canvas(canvas),
    )

    transition_trace_title = tk.Label(
        transition_trace_container,
        text="Transition Trace",
        font=TITLE_FONT,
        bg=TRANSITION_TRACE_TITLE_BG,
        fg=TRANSITION_TRACE_FG,
        relief=tk.FLAT,
        bd=2,
        padx=10,
        pady=5,
    )
    transition_trace_title.pack(side=tk.LEFT, fill=tk.Y)

    transition_trace_label = tk.Text(
        transition_trace_container,
        font=LABEL_FONT,
        bg=TRANSITION_TRACE_BG,
        fg=TRANSITION_TRACE_FG,
        relief=tk.FLAT,
        bd=2,
        padx=10,
        pady=5,
        wrap=tk.WORD,
        height=1,
    )
    transition_trace_label.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    transition_trace_label.config(state=tk.DISABLED)

    update_transition_display(transition_trace_label, reset_button, undo_button)

    state_name_entry: Entry = tk.Entry(left_button_frame)
    highlight_button: Button = tk.Button(
        left_button_frame,
        text="Enter State Name",
        state="disabled",
        command=lambda: enter_state(
            state_name_entry.get(),
            canvas,
            transition_trace_label,
            reset_button,
            undo_button,
            app,
        ),
    )

    button_show_graph: Button = tk.Button(
        left_button_frame,
        text="Show State Diagram Graph",
        state="disabled",
        command=show_state_diagram_graph,
    )

    reachability_button = tk.Button(
        left_button_frame,
        text="Reachability Analysis",
        state="disabled",
        command=lambda: on_reachability_analysis(
            current_transitions, initial_state_key, show_analysis_results
        ),
    )

    max_nodes_path = tk.Button(
        left_button_frame,
        text="Max Nodes Analysis",
        state="disabled",
        command=lambda: decide_graph_analysis(
            "node", current_transitions, initial_state_key, show_analysis_results
        ),
    )

    max_transition_path = tk.Button(
        left_button_frame,
        text="Max transitions Analysis",
        state="disabled",
        command=lambda: decide_graph_analysis(
            "transition", current_transitions, initial_state_key, show_analysis_results
        ),
    )

    load_button.pack(side=tk.LEFT, padx=(5, 25))
    state_name_entry.pack(side=tk.LEFT, padx=(0, 5))
    highlight_button.pack(side=tk.LEFT, padx=(0, 40))
    button_show_graph.pack(side=tk.LEFT, padx=(0, 5))
    reachability_button.pack(side=tk.LEFT, padx=(0, 5))
    max_nodes_path.pack(side=tk.LEFT, padx=(0, 5))
    max_transition_path.pack(side=tk.LEFT, padx=(0, 40))
    maximize_zoom_button.pack(side=tk.LEFT, padx=(0, 15))

    vertical_scroll_bar: Scrollbar = tk.Scrollbar(
        canvas_frame, orient=tk.VERTICAL, command=canvas.yview, bg=SCROLLBAR_BG
    )
    vertical_scroll_bar.grid(row=0, column=1, sticky="ns")
    canvas.configure(yscrollcommand=vertical_scroll_bar.set)

    horizontal_scroll_bar: Scrollbar = tk.Scrollbar(
        canvas_frame, orient=tk.HORIZONTAL, command=canvas.xview, bg=SCROLLBAR_BG
    )
    horizontal_scroll_bar.grid(row=1, column=0, sticky="ew")
    canvas.configure(xscrollcommand=horizontal_scroll_bar.set)

    canvas_frame.grid_rowconfigure(0, weight=1)
    canvas_frame.grid_columnconfigure(0, weight=1)

    canvas.bind("<Configure>", update_text_width())
    canvas.bind("<Control-MouseWheel>", lambda event: zoom(event, canvas))
    canvas.bind("<Control-Button-4>", lambda event: zoom(event, canvas))
    canvas.bind("<Control-Button-5>", lambda event: zoom(event, canvas))
    canvas.bind("<Command-MouseWheel>", lambda event: zoom(event, canvas))

    canvas.bind(
        "<MouseWheel>",
        lambda event: on_canvas_scroll(
            event,
            canvas,
        ),
    )
    canvas.bind(
        "<Button-1>",
        lambda event: on_canvas_click(
            event, canvas, transition_trace_label, reset_button, undo_button, app
        ),
    )

    def on_close():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            logging.info(APP_EXIT_MESSAGE)
            app.quit()
            app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_close)

    try:
        app.mainloop()
    except Exception as e:
        logging.error("Unhandled exception: %s", str(e))
        raise


if __name__ == "__main__":
    run_app()
