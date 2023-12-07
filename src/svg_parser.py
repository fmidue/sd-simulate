import re
import xml.etree.ElementTree as ET
from typing import Dict, List

ELEMENTS = []
STATE_HIERARCHY: Dict[str, List[str]] = {}


def identify_xml_type(root):
    g_elements = root.findall(".//{http://www.w3.org/2000/svg}g")
    has_id = any(g.get("id") is not None for g in g_elements)
    if has_id:
        return "Type1"
    else:
        return "Type2"


def parse_svg(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    result_list = []
    text_elements = root.findall(".//{http://www.w3.org/2000/svg}text")
    rect_elements = root.findall(".//{http://www.w3.org/2000/svg}rect")
    ellipse_elements = root.findall(".//{http://www.w3.org/2000/svg}ellipse")

    for text_element in text_elements:
        text_fill_color = text_element.get("fill")
        if text_fill_color != "#000000":
            matching_rect = None
            for rect_element in rect_elements:
                rect_stroke_match = rect_element.get("style")
                if f"stroke:{text_fill_color};" in rect_stroke_match:
                    matching_rect = rect_element
                    break
            if matching_rect is not None:
                state_name = text_element.text.strip()
                rect_x = float(matching_rect.get("x"))
                rect_y = float(matching_rect.get("y"))
                rect_width = float(matching_rect.get("width"))
                rect_height = float(matching_rect.get("height"))
                x1 = rect_x
                x2 = rect_x + rect_width
                y1 = rect_y
                y2 = rect_y + rect_height
                result_list.append((state_name, (x1, x2, y1, y2)))

    for i in range(len(ellipse_elements) - 1):
        outer_ellipse = ellipse_elements[i]
        inner_ellipse = ellipse_elements[i + 1]

        if outer_ellipse.get("cx") == inner_ellipse.get("cx") and outer_ellipse.get(
            "cy"
        ) == inner_ellipse.get("cy"):
            if (
                outer_ellipse.get("fill") == "none"
                and inner_ellipse.get("fill") != "none"
            ):
                cx, cy = float(outer_ellipse.get("cx")), float(outer_ellipse.get("cy"))
                rx, ry = float(outer_ellipse.get("rx")), float(outer_ellipse.get("ry"))
                end_state_bounds = (cx - rx, cx + rx, cy - ry, cy + ry)
                result_list.append(("[**]", end_state_bounds))

    result_list.sort(key=lambda x: (len(STATE_HIERARCHY.get(x[0], [])), x[1][0]))
    STATE_HIERARCHY.update(build_state_hierarchy(result_list))

    for state, hierarchy in STATE_HIERARCHY.items():
        print(f"State: {state}")
        print(f"Children: {hierarchy}")
        print()

    global ELEMENTS
    ELEMENTS = result_list


def svg_path_to_coords(path_str):
    x_values = []
    y_values = []

    commands = re.findall(
        r"([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)", path_str
    )

    current_x, current_y = 0, 0

    for command, data_str in commands:
        data = list(map(float, re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", data_str)))

        if command in "M":
            current_x, current_y = data[0], data[1]
            x_values.append(current_x)
            y_values.append(current_y)

        elif command in "h":
            for x in data:
                current_x = current_x + x
                x_values.append(current_x)

        elif command in "v":
            for y in data:
                current_y = current_y + y
                y_values.append(current_y)

        elif command in "c":
            current_x = current_x + data[4]
            current_y = current_y + data[5]
            x_values.append(current_x)
            y_values.append(current_y)

    if x_values and y_values:
        x1 = min(x_values)
        x2 = max(x_values)
        y1 = min(y_values)
        y2 = max(y_values)

        return x1, x2, y1, y2

    return None


def parse_svg2(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    result_list = []

    group_elements = root.findall(".//{http://www.w3.org/2000/svg}g")

    for group_element in group_elements:
        group_fill_color = group_element.get("fill")
        print(f"Group Fill Color: {group_fill_color}")
        if group_fill_color == "rgb(0,0,0)":
            print("here skipped black colored group")
            continue

        text_element = group_element.find(".//{http://www.w3.org/2000/svg}text")

        if text_element is not None:
            if text_element.text:
                state_name = text_element.text.strip()
            else:
                state_name = "''"
            print(f"Found Text Element: {state_name}")
        else:
            print("No Text Element found in group")
            continue

        related_path = None
        for path_element in root.findall(".//{http://www.w3.org/2000/svg}g"):
            path_stroke_color = path_element.get("stroke")

            if path_stroke_color is not None:
                path = path_element.find(".//{http://www.w3.org/2000/svg}path")
                print(f"Path Stroke Color: {path_stroke_color}")
                if path_stroke_color == group_fill_color:
                    related_path = path.get("d")
                    break

        if related_path:
            coordinates = svg_path_to_coords(related_path)
            if coordinates:
                result_list.append((state_name, coordinates))
            print(f"Added State: {state_name}")
            print(f"Related Path: {related_path}")
        else:
            print(f"No matching path found for state: {state_name}")

    for state, coordinates in result_list:
        print(f"State: {state}")
        print(f"Coordinates: {coordinates}")
        print()

    global STATE_HIERARCHY
    STATE_HIERARCHY = build_state_hierarchy(result_list)

    if result_list:
        max_x = max(coordinates[1] for _, coordinates in result_list)
        max_y = max(coordinates[3] for _, coordinates in result_list)
        print(f"Max X: {max_x}")
        print(f"Max Y: {max_y}")
    else:
        print("The selected SVG doesn't contain the expected elements.")

    for state, hierarchy in STATE_HIERARCHY.items():
        print(f"State: {state}")
        print(f"Children: {hierarchy}")
        print()

    global ELEMENTS
    ELEMENTS = result_list


def build_state_hierarchy(states):
    hierarchy = {state: [] for state, _ in states}

    states = sorted(states, key=lambda x: (x[1][1] - x[1][0]) * (x[1][3] - x[1][2]))

    for i, (child_state, child_coords) in enumerate(states):
        for j in range(i + 1, len(states)):
            parent_state, parent_coords = states[j]
            if (
                parent_coords[0] <= child_coords[0]
                and parent_coords[1] >= child_coords[1]
                and parent_coords[2] <= child_coords[2]
                and parent_coords[3] >= child_coords[3]
            ):
                hierarchy[parent_state].append(child_state)
                break

    return hierarchy


def check_state_type1(x, y):
    # print(f"Checking state for x={x}, y={y}")

    for element in reversed(ELEMENTS):
        x1, x2, y1, y2 = element[1]
        # print(f"Checking against x1={x1}, x2={x2}, y1={y1}, y2={y2}")
        if x1 <= x <= x2 and y1 <= y <= y2:
            print(f"Matched with {element[0]}")
            return element[0]
    print("Outside")
    return "Outside"


def check_state_type2(x, y, state=None, state_hierarchy=None):
    if state is None:
        state = "Outside"
    if state_hierarchy is None:
        state_hierarchy = []

    for element in ELEMENTS:
        x1, x2, y1, y2 = element[1]
        if x1 <= x <= x2 and y1 <= y <= y2:
            state = element[0]
            break

    if state not in state_hierarchy:
        state_hierarchy.append(state)
        parent_states = STATE_HIERARCHY.get(state, [])
        for parent_state in parent_states:
            check_state_type2(x, y, parent_state, state_hierarchy)

    return state_hierarchy


def find_active_states(state, visited=None):
    if visited is None:
        visited = set()

    if state in visited:
        return set()

    visited.add(state)
    marked_states = {state}

    for parent_state, child_states in STATE_HIERARCHY.items():
        if state in child_states:
            print(f"Marked state: {parent_state}")
            marked_states.add(parent_state)
            marked_states.update(find_active_states(parent_state, visited))

    return marked_states


def get_elements():
    return ELEMENTS


def get_hierarchy():
    return STATE_HIERARCHY
