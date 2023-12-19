from typing import Dict, List

current_scale = 1.0
last_scale = None
last_svg_content_hash = None
debug_mode = False
analysis_mode = False
xml_type = None
loaded_svg_content = None
MIN_WIDTH = 1
MIN_HEIGHT = 1
current_image = None
transition_trace = []
state_stack = []
is_svg_updated = False
hints_visible = False
current_state: Dict[str, List[str]] = {"active": [], "remembered": []}
initial_state_key = None
transitions = {}
original_width = None
original_height = None
svg_file_path = None
svg_rainbow_file_path = None

transition_trace_label = None
transitions_file_path = None
