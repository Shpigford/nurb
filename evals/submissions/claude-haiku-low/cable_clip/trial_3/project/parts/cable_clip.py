from nurb import *


@part
def cable_clip(bundle_diameter: float = 8.0):
	"""Screw-down cable clip for bundled cables.

	bundle_diameter: diameter of the cable bundle to hold, in mm
	"""
	# Fixed dimensions
	wall_thickness = 2.4
	base_thickness = 3.0
	channel_length = 12.0
	tab_length = 10.0
	tab_thickness = 3.0
	hole_diameter = 4.2

	# Derived dimensions
	channel_width = bundle_diameter + 0.4
	channel_depth = bundle_diameter

	# Total body dimensions
	body_width = wall_thickness + channel_width + wall_thickness
	body_height = base_thickness + channel_depth

	# Build the channel structure by creating and unioning parts
	# This creates a cleaner geometry with fewer artifacts than subtraction

	# Base platform
	base = Box(body_width, channel_length, base_thickness)

	# Left wall (sits on base)
	left_wall = Box(wall_thickness, channel_length, channel_depth)
	left_wall = left_wall.translate(Vector(-body_width/2 + wall_thickness/2, 0, base_thickness/2 + channel_depth/2))

	# Right wall (sits on base)
	right_wall = Box(wall_thickness, channel_length, channel_depth)
	right_wall = right_wall.translate(Vector(body_width/2 - wall_thickness/2, 0, base_thickness/2 + channel_depth/2))

	# Combine base and walls
	main_part = base + left_wall + right_wall

	# Create mounting tab (extends from outside of right wall)
	mount_tab = Box(tab_length, tab_thickness, tab_thickness)
	tab_y_offset = (channel_length - tab_thickness) / 2
	mount_tab = mount_tab.translate(Vector(body_width / 2 + tab_length / 2, tab_y_offset, 0))

	# Combine main part with mounting tab
	# Account for Box centering: main_body goes from -body_width/2 to +body_width/2
	# Tab should start where main_body ends, so translate by body_width/2 + tab_length/2
	combined = main_part + mount_tab

	# Create through-hole in the mounting tab (vertical, 4.2mm diameter)
	hole = Cylinder(hole_diameter / 2, tab_thickness + 0.2)
	# Position hole at center of mounting tab
	hole_x = body_width / 2 + tab_length / 2
	hole_y = tab_y_offset
	hole_z = 0  # Aligned with tab center
	hole = hole.translate(Vector(hole_x, hole_y, hole_z))

	# Subtract hole from combined part
	final_part = combined - hole

	# Polish exterior edges while preserving the square channel interior
	# The concave edges (channel interior) must stay square per spec
	bed = final_part.bounding_box().min.Z
	concave_edge_set = set(concave_edges(final_part))

	# Select edges above bed level that are not concave
	def is_polish_candidate(edge):
		if edge.bounding_box().min.Z <= bed + 0.1:
			return False  # Skip bed-level edges
		if edge in concave_edge_set:
			return False  # Skip concave channel edges
		return True

	edges_to_polish = final_part.edges().filter_by(is_polish_candidate)
	if list(edges_to_polish):
		final_part = polish(final_part, edges_to_polish, 1.0)

	return final_part
