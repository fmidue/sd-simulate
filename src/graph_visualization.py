import os
import platform
import subprocess

import globals
import logging
from config import STATE_DIAGRAM_GRAPH_PATH
from graphviz import Digraph
from utilities import clean_state_representation


def create_state_diagram_graph():
    graph = Digraph(comment="UML State Diagram")

    added_states = set()
    initial_state = globals.initial_state_key

    if initial_state:
        graph.node(
            "start",
            shape="circle",
            width=".15",
            height=".15",
            label="",
            style="filled",
            fillcolor="black",
        )
        graph.edge("start", clean_state_representation(initial_state))

    for source, dest_dict in globals.transitions.items():
        cleaned_source = clean_state_representation(source)

        if cleaned_source not in added_states:
            if source == "[**]":
                graph.node(
                    cleaned_source,
                    shape="doublecircle",
                    style="filled",
                    fillcolor="black",
                    width="0.015",
                    height="0.015",
                    fontsize="2",
                )
            else:
                graph.node(cleaned_source)
            added_states.add(cleaned_source)

        for dest, label_dict in dest_dict.items():
            cleaned_dest = clean_state_representation(dest)

            if cleaned_dest not in added_states:
                if dest == "[**]":
                    graph.node(
                        cleaned_dest,
                        shape="doublecircle",
                        style="filled",
                        fillcolor="black",
                        width="0.015",
                        height="0.015",
                        fontsize="2",
                    )
                else:
                    graph.node(cleaned_dest)
                added_states.add(cleaned_dest)

            for label, option_label in label_dict.items():
                graph.edge(cleaned_source, cleaned_dest, label=label)

    return graph


def show_state_diagram_graph():
    if not globals.transitions:
        logging.error("No transitions data available. Load transitions first.")
        return

    graph = create_state_diagram_graph()
    display_state_diagram_graph(graph)


def display_state_diagram_graph(graph):
    graph_file_path = STATE_DIAGRAM_GRAPH_PATH
    graph.save(graph_file_path)

    subprocess.run(["dot", "-Tpng", "-o", "state_diagram_graph.png", graph_file_path])

    image_path = os.path.abspath("state_diagram_graph.png")

    if platform.system() == "Darwin":
        subprocess.run(["open", "-a", "Preview", image_path])
    elif platform.system() == "Windows":
        subprocess.Popen(["start", "state_diagram_graph.png"], shell=True)
    elif platform.system() == "Linux":
        subprocess.run(["xdg-open", image_path])
    else:
        logging.error("Unsupported operating system.")
