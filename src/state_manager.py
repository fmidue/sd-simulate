import logging
from tkinter import messagebox

import globals
from svg_parser import get_hierarchy
from utilities import (
    ask_user_for_transition,
    file_state_representation,
    parse_state,
    state_representation,
    update_transition_display,
)


def read_transitions_from_file(file_path):
    globals.transitions = {}
    transition_counter = {}

    def add_transition(source, dest, label):
        source_key = file_state_representation(source)
        dest_key = file_state_representation(dest)

        if source_key not in globals.transitions:
            globals.transitions[source_key] = {}

        if dest_key not in globals.transitions[source_key]:
            globals.transitions[source_key][dest_key] = {label: "Option 1"}
        else:
            counter = transition_counter.get((source_key, dest_key), 1) + 1
            transition_counter[(source_key, dest_key)] = counter
            globals.transitions[source_key][dest_key][label] = f"Option {counter}"

    with open(file_path, "r") as file:
        for line in file.readlines():
            line = line.strip()

            if line.startswith("[*] -> "):
                state_str = line[6:].strip()
                active, remembered = parse_state(state_str)
                globals.current_state["active"] = active
                globals.current_state["remembered"] = remembered
                globals.initial_state_key = file_state_representation(state_str)
                globals.transitions[globals.initial_state_key] = {}
            elif "->" in line:
                parts = line.split("->")
                source_str = parts[0].strip()
                dest_and_label = parts[1].strip()
                dest_str, label = map(str.strip, dest_and_label.split(":"))
                add_transition(source_str, dest_str, label)

    return globals.current_state, globals.transitions


def state_parameter(state, transition_trace_label, reset_button, undo_button, parent):
    current_active_formatted = ",".join(globals.current_state["active"])
    current_remembered_formatted = (
        ",".join(globals.current_state["remembered"])
        if globals.current_state["remembered"]
        else None
    )

    if current_remembered_formatted:
        combined_transition_state = (
            f"{state}({current_active_formatted},{current_remembered_formatted})"
        )
    else:
        combined_transition_state = state

    available_transitions = globals.transitions.get(combined_transition_state, {})

    if globals.current_state["remembered"] == []:
        combined_transition_state = f"{state}({globals.current_state['active']})"

        if combined_transition_state in available_transitions:
            globals.hints_visible = False
            state_transitioned = state_handling(
                combined_transition_state,
                transition_trace_label,
                reset_button,
                undo_button,
                parent,
            )
        else:
            globals.hints_visible = False
            state_transitioned = state_handling(
                state,
                transition_trace_label,
                reset_button,
                undo_button,
                parent,
            )
    else:
        combined_transition_state = f"{state}({globals.current_state['remembered']})"
        current = state_representation(globals.current_state)

        if combined_transition_state in globals.transitions.get(current, {}):
            globals.hints_visible = False
            state_transitioned = state_handling(
                combined_transition_state,
                transition_trace_label,
                reset_button,
                undo_button,
                parent,
            )
        else:
            globals.hints_visible = False
            state_transitioned = state_handling(
                state,
                transition_trace_label,
                reset_button,
                undo_button,
                parent,
            )

    return state_transitioned


def state_select(
    state_condition,
    active_current,
    transition_trace_label,
    reset_button,
    undo_button,
    parent,
):
    state_changed = False

    if len(state_condition) == 1:
        chosen_transition = list(state_condition.items())[0][0]

    else:
        chosen_transition = ask_user_for_transition(state_condition, parent)

    if chosen_transition is not None:
        globals.state_stack.append(globals.current_state.copy())
        next_state = state_condition[chosen_transition]
        active, new_remembered = parse_state(next_state)
        if active != active_current:
            state_changed = True
        globals.current_state["active"] = active
        globals.current_state["remembered"] = new_remembered
        globals.transition_trace.append(chosen_transition)
        update_transition_display(transition_trace_label, reset_button, undo_button)
    return state_changed


def state_handling(state, transition_trace_label, reset_button, undo_button, parent):
    STATE_HIERARCHY = get_hierarchy()

    state_changed = False

    def collect_all_children(state_name, hierarchy):
        if state_name == "Outside":
            top_level_states = set(hierarchy.keys())
            for state, children in hierarchy.items():
                top_level_states.difference_update(children)
            return list(top_level_states)

        all_children = []
        children = hierarchy.get(state_name, [])
        for child in children:
            all_children.append(child)
            all_children.extend(collect_all_children(child, hierarchy))

        for element in all_children:
            if hierarchy.get(element):
                all_children.remove(element)

        return list(set(all_children))

    def is_part_of_combined_state(clicked_state, allowed_transitions):
        relevant_combined_states = []
        for transition_state in allowed_transitions:
            active_transition_states, _ = parse_state(transition_state)
            for active_state in active_transition_states:
                individual_states = active_state.split(",")
                if clicked_state in individual_states:
                    relevant_combined_states.append(transition_state)
        return relevant_combined_states

    current = state_representation(globals.current_state)

    active_clicked, remembered_clicked = parse_state(state)
    active_current, remembered_current = parse_state(current)

    children = collect_all_children(state, STATE_HIERARCHY)

    allowed_transitions = globals.transitions.get(current, {})
    combined_states = is_part_of_combined_state(state, allowed_transitions)

    if combined_states:
        chosen_transition = None
        transition_to_combined_state_map = {}

        if len(combined_states) > 1:
            for combined_state in combined_states:
                for transition_option in globals.transitions[current][combined_state]:
                    transition_to_combined_state_map[transition_option] = combined_state
            chosen_transition = ask_user_for_transition(
                transition_to_combined_state_map, parent
            )
        else:
            combined_state = combined_states[0]
            if isinstance(combined_state, list):
                combined_state = combined_state[0]
            if isinstance(globals.transitions[current][combined_state], dict):
                chosen_transition = ask_user_for_transition(
                    globals.transitions[current][combined_state], parent
                )
            else:
                chosen_transition = globals.transitions[current][combined_state]

        if chosen_transition is not None:
            target_combined_state = transition_to_combined_state_map.get(
                chosen_transition, combined_state
            )
            globals.state_stack.append(globals.current_state.copy())
            active_next, remembered_next = parse_state(target_combined_state)
            if "," in active_next[0]:
                active_next = active_next[0].split(",")
            globals.current_state["active"] = active_next
            globals.current_state["remembered"] = remembered_next
            globals.transition_trace.append(chosen_transition)
            update_transition_display(transition_trace_label, reset_button, undo_button)
            state_changed = True
            return state_changed
        else:
            return

    if state in allowed_transitions:
        if isinstance(allowed_transitions[state], dict):
            chosen_transition = ask_user_for_transition(
                allowed_transitions[state], parent
            )
        else:
            chosen_transition = allowed_transitions[state]

        if chosen_transition is not None:
            globals.state_stack.append(globals.current_state.copy())
            if active_clicked != active_current:
                state_changed = True
            globals.current_state["active"] = active_clicked
            globals.current_state["remembered"] = remembered_clicked
            globals.transition_trace.append(chosen_transition)
            update_transition_display(transition_trace_label, reset_button, undo_button)
    elif state in allowed_transitions:
        globals.state_stack.append(globals.current_state.copy())
        if active_clicked != active_current:
            state_changed = True
        globals.current_state["active"] = active_clicked
        globals.current_state["remembered"] = remembered_clicked
        globals.transition_trace.append(allowed_transitions[state])
        update_transition_display(transition_trace_label, reset_button, undo_button)
    elif state in STATE_HIERARCHY and children != []:
        allowed_transitions_from_children = {}

        for child in children:
            combined_states = is_part_of_combined_state(child, allowed_transitions)
            if combined_states:
                child = combined_states[0]

            for combined_state, transitions in allowed_transitions.items():
                if child in combined_state.split("(") or child == combined_state:
                    if isinstance(transitions, dict):
                        for option, transition_label in transitions.items():
                            allowed_transitions_from_children[option] = child
                    else:
                        allowed_transitions_from_children[transitions] = child

        if allowed_transitions_from_children:
            state_changed = state_select(
                allowed_transitions_from_outside,
                active_current,
                transition_trace_label,
                reset_button,
                undo_button,
                parent,
            )

    elif state == "Outside":
        outside_children = collect_all_children("Outside", STATE_HIERARCHY)

        allowed_transitions_from_outside = {}

        for top_level_state in outside_children:
            for target_state, transitions in globals.transitions.get(
                current, {}
            ).items():
                if isinstance(transitions, dict):
                    for option, transition_label in transitions.items():
                        allowed_transitions_from_outside[option] = target_state
                else:
                    allowed_transitions_from_outside[transitions] = target_state

        if allowed_transitions_from_outside:
            state_changed = state_select(
                allowed_transitions_from_outside,
                active_current,
                transition_trace_label,
                reset_button,
                undo_button,
                parent,
            )
    else:
        logging.error(f"No valid transitions found from {current} to {active_clicked}")
        messagebox.showinfo(
            "Invalid Transition",
            f"Cannot transition from {current} to (within) {state}",
        )

    return state_changed
