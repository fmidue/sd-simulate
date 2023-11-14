import tkinter as tk
from tkinter import Button, Canvas, Entry, Scrollbar

from GUI import (
    Enter_state,
    choose_file,
    maximize_visible_canvas,
    on_canvas_click,
    on_canvas_scroll,
    toggle_color_mode,
    zoom,
)

debug_mode = False

app = tk.Tk()
app.title("UML Diagram Viewer")

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
    command=lambda: Enter_state(state_name_entry.get(), canvas),
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
        highlight_button["state"] = "normal"
        maximize_zoom_button["state"] = "normal"
        if debug_mode:
            toggle_button["state"] = "normal"


load_button: Button = tk.Button(
    button_frame, text="Load UML Diagram", command=on_file_loaded
)
load_button.pack(side=tk.LEFT, padx=(5, 50))


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
canvas.bind("<Button-1>", lambda event: on_canvas_click(event, canvas))

app.mainloop()
