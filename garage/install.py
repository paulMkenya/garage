import frappe

from garage.setup_data import CHECK_IN_TERMS, LABOUR_ITEMS, TEMPLATES


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
	setup_workshop()
	frappe.db.commit()


def setup_workshop():
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	create_custom_fields(
		{
			dt: [
				{
					"fieldname": "repair_order",
					"label": "Repair Order",
					"fieldtype": "Link",
					"options": "Repair Order",
					"insert_after": "customer_name" if dt == "Sales Invoice" else "party_name",
					"read_only": 1,
					"no_copy": 1,
					"in_standard_filter": 1,
				}
			]
			for dt in ("Quotation", "Sales Invoice")
		},
		update=True,
	)

	for group in ("Garage Parts", "Garage Labour"):
		if not frappe.db.exists("Item Group", group):
			frappe.get_doc(
				{"doctype": "Item Group", "item_group_name": group, "parent_item_group": "All Item Groups"}
			).insert(ignore_permissions=True)

	for code, name in LABOUR_ITEMS:
		if not frappe.db.exists("Item", code):
			frappe.get_doc({
				"doctype": "Item", "item_code": code, "item_name": name, "item_group": "Garage Labour",
				"stock_uom": "Hour" if frappe.db.exists("UOM", "Hour") else "Nos",
				"is_stock_item": 0, "include_item_in_manufacturing": 0,
			}).insert(ignore_permissions=True)

	if not frappe.db.exists("Kanban Board", "Workshop Board"):
		from garage.garage.doctype.repair_order.repair_order import RO_STATUSES

		board = frappe.new_doc("Kanban Board")
		board.kanban_board_name = "Workshop Board"
		board.reference_doctype = "Repair Order"
		board.field_name = "status"
		board.private = 0
		for status in RO_STATUSES:
			board.append("columns", {"column_name": status, "status": "Active", "indicator": "Gray"})
		board.insert(ignore_permissions=True)
	frappe.db.set_value(
		"Kanban Board",
		"Workshop Board",
		"fields",
		'["customer_name", "vehicle_description", "technician_name", "bay", "promised_time"]',
	)
