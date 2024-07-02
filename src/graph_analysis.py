from tkinter import messagebox

import globals

current_best_node = []
current_best_path = []


def perform_reachability_analysis(transitions, initial_state):
    visited = set()
    stack = [initial_state]

    while stack:
        state = stack.pop()
        if state not in visited:
            visited.add(state)
            for next_state in transitions.get(state, {}):
                stack.append(next_state)

    globals.graph_states = visited
    unreachable_states = set(transitions.keys()) - visited
    return visited, unreachable_states


def on_reachability_analysis(transitions, initial_state_key, show_results):
    if initial_state_key is None:
        messagebox.showerror("Error", "Initial state not set.")
        return

    reachable_states, unreachable_states = perform_reachability_analysis(
        transitions, initial_state_key
    )

    if unreachable_states:
        results = f"Unreachable States: {unreachable_states}"
        show_results("Reachability Analysis:", results)

    else:
        results = "All states are reachable from the initial state."
        show_results("Reachability Analysis:", results)


def decide_graph_analysis(mode, transitions, initial_state_key, show_results):
    if len(globals.graph_states) <= 15:
        perform_euler_hamilton_walk(mode, transitions, initial_state_key, show_results)
    else:
        messagebox.showinfo(
            "UML Diagram has too many States",
            "Performing longest Path analysis instead",
        )
        if mode == "node":
            perform_longest_path_analysis(transitions, initial_state_key, show_results)
        else:
            perform_max_transition_path_analysis(
                transitions, initial_state_key, show_results
            )


def perform_euler_hamilton_walk(mode, transitions, initial_state_key, show_results):
    global current_best_node
    global current_best_path
    current_best_node = []
    current_best_path = []

    def find_longest_paths(
        current_state,
        path,
        visited,
        recursion_depth,
    ):
        global current_best_node
        global current_best_path
        visited.append(current_state)

        if mode == "node":
            if len(set(visited)) > len(set(current_best_node)):
                current_best_node = visited
                current_best_path = path
            elif len(set(visited)) == len(set(current_best_node)):
                if len(path) < len(current_best_path):
                    current_best_node = visited
                    current_best_path = path
        elif mode == "transition":
            if len(set(path)) > len(set(current_best_path)):
                current_best_node = visited
                current_best_path = path
            elif len(set(path)) == len(set(current_best_path)):
                if len(path) < len(current_best_path):
                    current_best_node = visited
                    current_best_path = path

        if recursion_depth < globals.MAXIMUM_RECURSION_DEPTH:
            for next_state, labels in transitions.get(current_state, {}).items():
                for label in labels:
                    new_path = path + [(current_state, next_state, label)]
                    find_longest_paths(
                        next_state,
                        new_path,
                        visited.copy(),
                        recursion_depth + 1,
                    )

    find_longest_paths(initial_state_key, [], [], 0)

    transition_sequences = []
    for path in current_best_path:
        transition_sequences.append(path[2])

    show_results(
        "Maximum " + mode + " analysis:",
        "\n" + " ".join(current_best_node) + "\n" + "->".join(transition_sequences),
    )


def perform_longest_path_analysis(transitions, initial_state_key, show_results):
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
        sequence = [f"{label}" for src, dest, label in path]
        transition_sequences.append(sequence)

    transition_sequences_str = [" -> ".join(seq) for seq in transition_sequences]

    results = "\n".join(transition_sequences_str)
    show_results("Longest Path Analysis:", results)


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
            print(len(max_path))
    return max_path


def perform_max_transition_path_analysis(transitions, initial_state_key, show_results):
    print("reached1")
    max_transition_path = find_max_transition_path(
        transitions, initial_state_key, [], set()
    )

    if not max_transition_path:
        results = "No path found that traverses every transition at least once."
        show_results("Max Transition Path Analysis:", results)
        return

    transition_sequence = [f"{label}" for src, dest, label in max_transition_path]
    results = " -> ".join(transition_sequence)
    show_results("Max Transition Path Analysis:", results)
