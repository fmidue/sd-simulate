import logging
import xml.etree.ElementTree as ET

from typing import Dict, List
from config import DEFAULT_TEXT_COLOR, SVG_NAMESPACE, XML_TYPE_1, XML_TYPE_2
from utilities import svg_path_to_coords

ELEMENTS = []
STATE_HIERARCHY: Dict[str, List[str]] = {}


def identify_xml_type(root):
    g_elements = root.findall(f".//{SVG_NAMESPACE}g")
    has_id = any(g.get("id") is not None for g in g_elements)
    if has_id:
        return XML_TYPE_1
    else:
        return XML_TYPE_2


def parse_svg(file_path):
    global ELEMENTS, STATE_HIERARCHY
    tree = ET.parse(file_path)
    root = tree.getroot()
    result_list = []
    text_elements = root.findall(".//{http://www.w3.org/2000/svg}text")
    rect_elements = root.findall(".//{http://www.w3.org/2000/svg}rect")
    ellipse_elements = root.findall(".//{http://www.w3.org/2000/svg}ellipse")

    for text_element in text_elements:
        text_fill_color = text_element.get("fill")
        if text_fill_color != DEFAULT_TEXT_COLOR:
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

    for i in range(len(ellipse_elements)):
        outer_ellipse = ellipse_elements[i]
        for j in range(len(ellipse_elements)):
            if i == j:
                continue

            inner_ellipse = ellipse_elements[j]
            outer_cx, outer_cy = float(outer_ellipse.get("cx")), float(
                outer_ellipse.get("cy")
            )
            outer_rx, outer_ry = float(outer_ellipse.get("rx")), float(
                outer_ellipse.get("ry")
            )

            inner_cx, inner_cy = float(inner_ellipse.get("cx")), float(
                inner_ellipse.get("cy")
            )
            inner_rx, inner_ry = float(inner_ellipse.get("rx")), float(
                inner_ellipse.get("ry")
            )

            if (
                outer_cx - outer_rx <= inner_cx - inner_rx
                and outer_cx + outer_rx >= inner_cx + inner_rx
                and outer_cy - outer_ry <= inner_cy - inner_ry
                and outer_cy + outer_ry >= inner_cy + inner_ry
            ):
                end_state_bounds = (
                    outer_cx - outer_rx,
                    outer_cx + outer_rx,
                    outer_cy - outer_ry,
                    outer_cy + outer_ry,
                )
                result_list.append(("[**]", end_state_bounds))
                break

    result_list.sort(key=lambda x: (len(STATE_HIERARCHY.get(x[0], [])), x[1][0]))
    STATE_HIERARCHY.update(build_state_hierarchy(result_list))

    ELEMENTS = result_list

    return ELEMENTS, STATE_HIERARCHY


def parse_svg2(file_path):
    global ELEMENTS, STATE_HIERARCHY
    tree = ET.parse(file_path)
    root = tree.getroot()
    result_list = []
    colored_list = []
    text_list = []
    end_state = None
    end_state_color = None

    group_elements = root.findall(".//{http://www.w3.org/2000/svg}g")

    for group_element in group_elements:
        group_fill_color = group_element.get("fill")
        if group_fill_color != "rgb(0,0,0)":
            colored_list.append(group_fill_color)
        else:
            continue

        text_element = group_element.find(".//{http://www.w3.org/2000/svg}text")

        if text_element is not None:
            if text_element.text:
                text_list.append(text_element.text)
                state_name = text_element.text.strip()
        else:
            end_state_color = group_fill_color
            continue

        related_path = None
        for path_element in root.findall(".//{http://www.w3.org/2000/svg}g"):
            path_stroke_color = path_element.get("stroke")
            if path_stroke_color is not None:
                path = path_element.find(".//{http://www.w3.org/2000/svg}path")
                if path_stroke_color == group_fill_color:
                    related_path = path.get("d")

        if related_path:
            coordinates = svg_path_to_coords(related_path)
            if coordinates:
                result_list.append((state_name, coordinates))
        else:
            logging.error(f"No matching path found for state: {state_name}")

    for group_element in group_elements:
        path_stroke_color = group_element.get("stroke")
        if path_stroke_color == end_state_color and path_stroke_color != "rgb(0,0,0)":
            path = group_element.find(".//{http://www.w3.org/2000/svg}path")
            if path is not None:
                end_state = path.get("d")
                coordinates = svg_path_to_coords(end_state)
                if coordinates:
                    result_list.append(("[**]", coordinates))
            break

    global STATE_HIERARCHY
    STATE_HIERARCHY = build_state_hierarchy(result_list)

    if not result_list:
        logging.error("The selected SVG doesn't contain the expected elements.")

    ELEMENTS = result_list

    return ELEMENTS, STATE_HIERARCHY


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
    for element in reversed(ELEMENTS):
        x1, x2, y1, y2 = element[1]
        if x1 <= x <= x2 and y1 <= y <= y2:
            return element[0]
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
            marked_states.add(parent_state)
            marked_states.update(find_active_states(parent_state, visited))

    return marked_states


def get_elements():
    return ELEMENTS


def get_hierarchy():
    return STATE_HIERARCHY
