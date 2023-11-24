import atexit
import logging
import tkinter as tk
from tkinter import Button, Canvas, Entry, Scrollbar, messagebox

from GUI import (
    choose_file,
    enter_state,
    maximize_visible_canvas,
    on_canvas_click,
    on_canvas_scroll,
    reset_trace,
    show_hints,
    toggle_color_mode,
    undo_last_transition,
    update_transition_display,
    zoom,
)

logging.basicConfig(
    filename="app.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s:%(message)s",
)


def on_exit():
    print("Application is exiting...")


atexit.register(on_exit)


debug_mode = False


def run_app():
    global app, transition_trace_label
    app = tk.Tk()
    app.title("UML Diagram Viewer")

    trace_frame = tk.Frame(app)
    trace_frame.pack(side=tk.BOTTOM, fill=tk.X)

    left_trace_frame: tk.Frame = tk.Frame(trace_frame)
    left_trace_frame.pack(side=tk.LEFT)

    right_trace_frame: tk.Frame = tk.Frame(trace_frame)
    right_trace_frame.pack(side=tk.RIGHT)

    transition_trace_label = tk.Label(
        left_trace_frame,
        text="Transition Trace: ",
        font=("Helvetica", 10, "bold"),
        bg="lightgray",
        fg="black",
        relief=tk.FLAT,
        bd=2,
        padx=10,
        pady=5,
    )
    transition_trace_label.pack()

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
    undo_button.pack(side=tk.LEFT, padx=(0, 10))

    update_transition_display(transition_trace_label, reset_button, undo_button)

    button_frame = tk.Frame(app)
    button_frame.pack(side=tk.TOP, fill=tk.X)

    left_button_frame: tk.Frame = tk.Frame(button_frame)
    left_button_frame.pack(side=tk.LEFT)

    right_button_frame: tk.Frame = tk.Frame(button_frame)
    right_button_frame.pack(side=tk.RIGHT)

    canvas_frame: tk.Frame = tk.Frame(app)
    canvas_frame.pack(fill=tk.BOTH, expand=True)

    canvas: Canvas = tk.Canvas(canvas_frame, bg="white")
    canvas.grid(row=0, column=0, sticky="nsew")

    state_name_entry: Entry = tk.Entry(right_button_frame)
    highlight_button: Button = tk.Button(
        right_button_frame,
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
    maximize_zoom_button: Button = tk.Button(
        right_button_frame,
        text="Full View",
        state="disabled",
        command=lambda: maximize_visible_canvas(canvas),
    )
    toggle_button: Button = tk.Button(
        right_button_frame,
        text="Toggle Color Mode",
        state="disabled",
        command=lambda: toggle_color_mode(canvas),
    )

    if debug_mode:
        toggle_button.pack(side=tk.RIGHT)

    def on_file_loaded():
        global transition_trace
        if choose_file(canvas, transition_trace_label, reset_button, undo_button):
            highlight_button["state"] = "normal"
            maximize_zoom_button["state"] = "normal"
            hint_button["state"] = "normal"
            reset_button["state"] = "disabled"
            undo_button["state"] = "disabled"
            if debug_mode:
                toggle_button["state"] = "normal"

    load_button: Button = tk.Button(
        left_button_frame, text="Load UML Diagram", command=on_file_loaded
    )
    load_button.pack(side=tk.LEFT, padx=(5, 5))

    state_name_entry.pack(side=tk.LEFT, padx=(0, 5))
    highlight_button.pack(side=tk.LEFT, padx=(0, 50))
    maximize_zoom_button.pack(side=tk.LEFT, padx=(0, 1))
    toggle_button.pack(padx=(0, 25))

    vertical_scroll_bar: Scrollbar = tk.Scrollbar(
        canvas_frame, orient=tk.VERTICAL, command=canvas.yview, bg="gray"
    )
    vertical_scroll_bar.grid(row=0, column=1, sticky="ns")
    canvas.configure(yscrollcommand=vertical_scroll_bar.set)

    horizontal_scroll_bar: Scrollbar = tk.Scrollbar(
        canvas_frame, orient=tk.HORIZONTAL, command=canvas.xview, bg="gray"
    )
    horizontal_scroll_bar.grid(row=1, column=0, sticky="ew")
    canvas.configure(xscrollcommand=horizontal_scroll_bar.set)

    canvas_frame.grid_rowconfigure(0, weight=1)
    canvas_frame.grid_columnconfigure(0, weight=1)

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
        """Function to handle the window close event."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            logging.info("Application is exitinsg...")
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
