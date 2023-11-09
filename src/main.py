import tkinter as tk
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

load_button = tk.Button(
    button_frame, text="Load UML Diagram", command=lambda: choose_file(canvas)
)
load_button.pack()

canvas_frame = tk.Frame(app)
canvas_frame.pack(fill=tk.BOTH, expand=True)

canvas: tk.Canvas = tk.Canvas(canvas_frame, bg="white")

canvas.grid(row=0, column=0, sticky="nsew")

if debug_mode:
    toggle_button = tk.Button(
        button_frame,
        text="Toggle Color Mode",
        command=lambda: toggle_color_mode(canvas),
    )
    toggle_button.pack()

state_name_entry = tk.Entry(button_frame)
state_name_entry.pack()
highlight_button = tk.Button(
    button_frame,
    text="Enter state name",
    command=lambda: Enter_state(state_name_entry.get(), canvas),
)
highlight_button.pack()

maximize_zoom_button = tk.Button(
    button_frame,
    text="Maximize Zoom",
    command=lambda: maximize_visible_canvas(canvas),
)
maximize_zoom_button.pack()

vertical_scroll_bar = tk.Scrollbar(
    canvas_frame, orient=tk.VERTICAL, command=canvas.yview, bg="gray"
)
vertical_scroll_bar.grid(row=0, column=1, sticky="ns")
canvas.configure(yscrollcommand=vertical_scroll_bar.set)

horizontal_scroll_bar = tk.Scrollbar(
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
