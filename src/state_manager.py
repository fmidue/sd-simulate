from tkinter import messagebox

import globals
from utilities import (
    file_state_representation,
    state_representation,
    parse_state,
    ask_user_for_transition,
    update_transition_display,
)
from svg_parser import get_hierarchy


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
            option_label = f"Option {counter}"
            globals.transitions[source_key][dest_key][label] = option_label

    with open(file_path, "r") as file:
        for line in file.readlines():
            line = line.strip()

            if line.startswith("[*] -> "):
                print("Initial state line found:", line)
                state_str = line[6:].strip()
                active, remembered = parse_state(state_str)
                globals.current_state["active"] = active
                globals.current_state["remembered"] = remembered
                globals.initial_state_key = file_state_representation(state_str)
                print("Initial state line found 2:", globals.initial_state_key)
                globals.transitions[globals.initial_state_key] = {}
            elif "->" in line:
                parts = line.split("->")
                source_str = parts[0].strip()
                dest_and_label = parts[1].strip()
                dest_str, label = map(str.strip, dest_and_label.split(":"))
                add_transition(source_str, dest_str, label)

    return globals.current_state, globals.transitions


def state_parameter(state, transition_trace_label, reset_button, undo_button, parent):
    print(f"ON CANVAS CLICKED STATE: {state}")

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

    print(f"combined_transition_state: {combined_transition_state}")

    available_transitions = globals.transitions.get(9, {})

    if globals.current_state["remembered"] == []:
        combined_transition_state = f"{state}({globals.current_state['active']})"

        for transition in available_transitions:
            print(f"ON CANVAS 1: {transition}")
        if combined_transition_state in available_transitions:
            print("ON CANVAS 1 - CASE 1")
            globals.hints_visible = False
            state_transitioned = state_handling(
                combined_transition_state,
                transition_trace_label,
                reset_button,
                undo_button,
                parent,
            )
        else:
            print("ON CANVAS 1 - CASE 2")
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

        print(
            f"ON CANVAS 2 TEST 3: combined_transition_state: {combined_transition_state} From current state : {current}"
        )

        for transition in globals.transitions.get(current, {}):
            print(f"ON CANVAS 2: {transition}")

        if combined_transition_state in globals.transitions.get(current, {}):
            print("ON CANVAS 2 - CASE 1")
            globals.hints_visible = False
            state_transitioned = state_handling(
                combined_transition_state,
                transition_trace_label,
                reset_button,
                undo_button,
                parent,
            )
        else:
            print("ON CANVAS 2 - CASE 2")
            globals.hints_visible = False
            state_transitioned = state_handling(
                state,
                transition_trace_label,
                reset_button,
                undo_button,
                parent,
            )

    return state_transitioned


def state_handling(state, transition_trace_label, reset_button, undo_button, parent):
    STATE_HIERARCHY = get_hierarchy()

    state_changed = False

    def collect_all_children(state_name, hierarchy):
        all_children = []
        children = hierarchy.get(state_name, [])
        for child in children:
            print(f"CHILD TEST: {child}")
            all_children.append(child)
            all_children.extend(collect_all_children(child, hierarchy))

        for element in all_children:
            if hierarchy.get(element):
                all_children.remove(element)

        return all_children

    def is_part_of_combined_state(clicked_state, allowed_transitions):
        for transition_state in allowed_transitions:
            active_transition_states, _ = parse_state(transition_state)
            for active_state in active_transition_states:
                individual_states = active_state.split(",")
                if clicked_state in individual_states:
                    return transition_state
        return None

    current = globals.current_state

    current = state_representation(globals.current_state)
    print(f"Current State : {current}")
    print(f"Clicked State : {state}")
    print("============================")

    active_clicked, remembered_clicked = parse_state(state)
    active_current, remembered_current = parse_state(current)

    children = collect_all_children(state, STATE_HIERARCHY)
    print(f"Children : {children}")

    if state != "Outside":
        allowed_transitions = globals.transitions.get(current, {})
        print(
            f"Clicked State: {state}, Allowed Transitions from {current}: {allowed_transitions}"
        )

        transition_state = is_part_of_combined_state(
            state, globals.transitions.get(current, {})
        )
        print(f"Transition state after checking combined states: {transition_state}")

        print(f"state: {state} in allowed_transitions: {allowed_transitions}")
        if transition_state in globals.transitions.get(current, {}):
            print(
                f"Transition state after checking combined states: {transition_state}"
            )
            chosen_transition = None
            if isinstance(globals.transitions[current][transition_state], dict):
                chosen_transition = ask_user_for_transition(
                    globals.transitions[current][transition_state], parent
                )
            else:
                chosen_transition = globals.transitions[current][transition_state]

            if chosen_transition is not None:
                print(f"Handling transition to combined state {transition_state}")
                globals.state_stack.append(globals.current_state.copy())
                active_next, remembered_next = parse_state(transition_state)
                if "," in active_next[0]:
                    active_next = active_next[0].split(",")
                globals.current_state["active"] = active_next
                globals.current_state["remembered"] = remembered_next
                globals.transition_trace.append(chosen_transition)
                update_transition_display(
                    transition_trace_label, reset_button, undo_button
                )
                state_changed = True
                print(f"Transition: {globals.current_state}")
                return state_changed

        if state in allowed_transitions:
            if isinstance(allowed_transitions[state], dict):
                chosen_transition = ask_user_for_transition(
                    allowed_transitions[state], parent
                )
            else:
                chosen_transition = allowed_transitions[state]

            if chosen_transition is not None:
                print(f"CASE 1 - Handling dictionary transition {state}")
                globals.state_stack.append(globals.current_state.copy())
                if active_clicked != active_current:
                    state_changed = True
                    print("STATE CHANGED")
                globals.current_state["active"] = active_clicked
                globals.current_state["remembered"] = remembered_clicked
                globals.transition_trace.append(chosen_transition)
                update_transition_display(
                    transition_trace_label, reset_button, undo_button
                )
                print(f"Transition: {globals.current_state}")
        elif state in allowed_transitions:
            print(f"CASE 2 - Handling direct transition {active_clicked}")
            globals.state_stack.append(globals.current_state.copy())
            if active_clicked != active_current:
                state_changed = True
                print("STATE CHANGED")
            globals.current_state["active"] = active_clicked
            globals.current_state["remembered"] = remembered_clicked
            globals.transition_trace.append(allowed_transitions[state])
            update_transition_display(transition_trace_label, reset_button, undo_button)
            print(f"Transition: {globals.current_state}")
        elif state in STATE_HIERARCHY and children != []:
            print(
                f"CASE 3 - Handling transition from complex or hierarchical state: {active_current}"
            )
            allowed_transitions_from_children = {}

            for child in children:
                if child in allowed_transitions:
                    child_transitions = allowed_transitions[child]
                    if isinstance(child_transitions, dict):
                        for option, transition_label in child_transitions.items():
                            option_key = option
                            print(f"Child: {child} - Transition_label: {option}")
                            allowed_transitions_from_children[option_key] = child
                else:
                    allowed_transitions_from_children[child_transitions] = child
                print(
                    f"allowed_transitions_from_children: {allowed_transitions_from_children}"
                )

            if allowed_transitions_from_children:
                chosen_transition = ask_user_for_transition(
                    allowed_transitions_from_children, parent
                )
                if chosen_transition is not None:
                    globals.state_stack.append(globals.current_state.copy())
                    next_state = allowed_transitions_from_children[chosen_transition]
                    print(f"Chooen next state: {next_state}")
                    active, new_remembered = parse_state(next_state)
                    if active != active_current:
                        state_changed = True
                        print("STATE CHANGED")
                    globals.current_state["active"] = active
                    globals.current_state["remembered"] = new_remembered
                    globals.transition_trace.append(chosen_transition)
                    update_transition_display(
                        transition_trace_label, reset_button, undo_button
                    )
        else:
            print(f"No valid transitions found from {current} to {active_clicked}")
            messagebox.showinfo(
                "Invalid Transition",
                f"Cannot transition from {current} to {state}",
            )
            print("Invalid transition. Ignoring click.")
    else:
        messagebox.showinfo("Clicked Outside", "Please choose a valid state")
        print("Outside")

    return state_changed
