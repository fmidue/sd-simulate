from graphviz import Digraph
from tkinter import messagebox


def perform_reachability_analysis(transitions, initial_state):
    visited = set()
    stack = [initial_state]

    while stack:
        state = stack.pop()
        if state not in visited:
            visited.add(state)
            for next_state in transitions.get(state, {}):
                stack.append(next_state)

    unreachable_states = set(transitions.keys()) - visited
    return visited, unreachable_states


def on_reachability_analysis(transitions, initial_state_key):
    print("initial_state_key", initial_state_key)
    if initial_state_key is None:
        messagebox.showerror("Error", "Initial state not set.")
        return

    reachable_states, unreachable_states = perform_reachability_analysis(
        transitions, initial_state_key
    )

    if unreachable_states:
        messagebox.showinfo(
            "Reachability Analysis", f"Unreachable States: {unreachable_states}"
        )
    else:
        messagebox.showinfo(
            "Reachability Analysis", "All states are reachable from the initial state."
        )


def show_reachability_graph(transitions, reachable_states, unreachable_states):
    graph = Digraph(comment="Reachability Analysis")

    for state in transitions.keys():
        if state in reachable_states:
            graph.node(state, color="green")
        elif state in unreachable_states:
            graph.node(state, color="red")

    for source, dest_dict in transitions.items():
        for dest in dest_dict:
            graph.edge(source, dest)

    graph.render("reachability_analysis", view=True, format="png")


def perform_longest_path_analysis(transitions, initial_state_key):
    def find_longest_paths(current_state, path, visited):
        visited.add(current_state)
        paths = []
        for next_state, labels in transitions.get(current_state, {}).items():
            if next_state not in visited:
                for label in labels:
                    new_path = path + [(current_state, next_state, label)]
                    paths.extend(
                        find_longest_paths(next_state, new_path, visited.copy())
                    )
        return paths if paths else [path]

    longest_paths = find_longest_paths(initial_state_key, [], set())
    max_length = max(len(path) for path in longest_paths)
    longest_paths = [path for path in longest_paths if len(path) == max_length]

    transition_sequences = []
    for path in longest_paths:
        sequence = [f"{src}->{dest} ({label})" for src, dest, label in path]
        transition_sequences.append(sequence)

    transition_sequences_str = [" , ".join(seq) for seq in transition_sequences]
    messagebox.showinfo("Longest Path Analysis", "\n".join(transition_sequences_str))


def find_max_transition_path(transitions, current_state, path, visited_transitions):
    max_path = path
    for next_state, labels in transitions.get(current_state, {}).items():
        for label in labels:
            transition = (current_state, next_state, label)
            if transition not in visited_transitions:
                new_visited_transitions = visited_transitions | {transition}
                new_path = path + [transition]
                result_path = find_max_transition_path(
                    transitions, next_state, new_path, new_visited_transitions
                )
                if len(result_path) > len(max_path):
                    max_path = result_path
    return max_path


def perform_max_transition_path_analysis(transitions, initial_state_key):
    max_transition_path = find_max_transition_path(
        transitions, initial_state_key, [], set()
    )

    if not max_transition_path:
        messagebox.showinfo(
            "Max Transition Path Analysis",
            "No path found that traverses every transition at least once.",
        )
        return

    transition_sequence = [
        f"{src}->{dest} ({label})" for src, dest, label in max_transition_path
    ]
    messagebox.showinfo(
        "Max Transition Path Analysis", " , ".join(transition_sequence)
    )
