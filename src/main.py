import tkinter as tk
from tkinter import Button, Canvas, Entry, Scrollbar

from GUI import (
    Enter_state,
    choose_file,
    maximize_visible_canvas,
    on_canvas_click,
    on_canvas_scroll,
    toggle_color_mode,
    Simulation_mode,
    zoom,
    update_transition_display,
    simulation_mode,
    show_hints,
)


debug_mode = False

app = tk.Tk()
app.title("UML Diagram Viewer")


trace_frame = tk.Frame(app)
trace_frame.pack(side=tk.BOTTOM, fill=tk.X)


left_trace_frame: tk.Frame = tk.Frame(trace_frame)
left_trace_frame.pack(side=tk.LEFT)

right_trace_frame: tk.Frame = tk.Frame(trace_frame)
right_trace_frame.pack(side=tk.RIGHT)


global transition_trace_label
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
update_transition_display(transition_trace_label)


def toggle_trace_frame(show):
    if show:
        trace_frame.pack(side=tk.BOTTOM, fill=tk.X)
    else:
        trace_frame.pack_forget()


toggle_trace_frame(simulation_mode)

hint_button = tk.Button(
    right_trace_frame, text="Hint", command=lambda: show_hints(canvas)
)
hint_button.pack()


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
    command=lambda: Enter_state(state_name_entry.get(), canvas, transition_trace_label),
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
    if choose_file(canvas):
        Simulation_button["state"] = "normal"
        highlight_button["state"] = "normal"
        maximize_zoom_button["state"] = "normal"
        if debug_mode:
            toggle_button["state"] = "normal"


load_button: Button = tk.Button(
    left_button_frame, text="Load UML Diagram", command=on_file_loaded
)
load_button.pack(side=tk.LEFT, padx=(5, 5))
Simulation_button: Button = tk.Button(
    left_button_frame,
    text="Simulation Mode",
    state="disabled",
    command=lambda: Simulation_mode(canvas),
)
Simulation_button.pack(padx=(0, 50))


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

canvas.bind("<MouseWheel>", lambda event: on_canvas_scroll(event, canvas))
canvas.bind(
    "<Button-1>", lambda event: on_canvas_click(event, canvas, transition_trace_label)
)
Simulation_button["command"] = lambda: Simulation_mode(
    canvas, toggle_trace_frame, Simulation_button
)


app.mainloop()
