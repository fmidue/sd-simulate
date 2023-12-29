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


def on_reachability_analysis(transitions, initial_state_key, show_results):
    print("initial_state_key", initial_state_key)
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
    return max_path


def perform_max_transition_path_analysis(transitions, initial_state_key, show_results):
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
