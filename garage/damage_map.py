import os

import frappe

SEVERITY_COLOURS = {"Minor": "#f5b301", "Moderate": "#f07c00", "Severe": "#d92d20"}


def _base_svg() -> str:
	path = frappe.get_app_path("garage", "public", "images", "car_diagram.svg")
	with open(path) as f:
		return f.read()


def damage_map_svg(doc, width: str = "100%") -> str:
	"""Car diagram with numbered damage marks, for print formats."""
	marks = []
	for m in doc.get("damage_marks") or []:
		colour = SEVERITY_COLOURS.get(m.severity, "#d92d20")
		marks.append(
			f'<g><circle cx="{m.x or 0}" cy="{m.y or 0}" r="16" fill="{colour}" stroke="#fff" stroke-width="3"/>'
			f'<text x="{m.x or 0}" y="{(m.y or 0) + 6}" text-anchor="middle" font-size="17" font-weight="700" '
			f'fill="#fff" font-family="Arial">{int(m.mark_no or 0)}</text></g>'
		)
	svg = _base_svg().replace("<!--MARKS-->", "".join(marks))
	return svg.replace('width="100%"', f'width="{width}"', 1)
