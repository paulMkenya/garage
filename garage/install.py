import frappe

from garage.setup_data import CHECK_IN_TERMS, TEMPLATES


def after_install():
	for name, (description, is_default, items) in TEMPLATES.items():
		if frappe.db.exists("Vehicle Check In Template", name):
			continue
		doc = frappe.new_doc("Vehicle Check In Template")
		doc.template_name = name
		doc.description = description
		doc.is_default = is_default
		for category, check, *rest in items:
			doc.append("items", {"category": category, "check_item": check, "help_text": rest[0] if rest else None})
		doc.insert(ignore_permissions=True)

	settings = frappe.get_single("Garage Settings")
	changed = False
	if not settings.default_check_in_template:
		settings.default_check_in_template = next(n for n, t in TEMPLATES.items() if t[1])
		changed = True
	if not settings.check_in_terms:
		settings.check_in_terms = CHECK_IN_TERMS
		changed = True
	if changed:
		settings.flags.ignore_mandatory = True
		settings.save(ignore_permissions=True)
	frappe.db.commit()
