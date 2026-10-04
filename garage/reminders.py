import frappe
from frappe import _
from frappe.utils import add_days, add_months, cint, getdate, today

SERVICE_LABOUR = ("LAB-SERVICE",)


def is_service_visit(ro) -> bool:
	if "service" in (ro.service_type or "").lower():
		return True
	return any(row.item_code in SERVICE_LABOUR and row.approved for row in ro.items)


def update_service_due(gate_pass):
	"""Called when a vehicle is released: roll the next-service date/km forward after a service."""
	ro = frappe.get_doc("Repair Order", gate_pass.repair_order)
	if not is_service_visit(ro):
		return
	v = frappe.get_doc("Garage Vehicle", gate_pass.vehicle)
	km = cint(gate_pass.exit_odometer) or cint(ro.odometer)
	values = {
		"last_service_date": today(),
		"last_service_km": km,
		"next_service_date": add_months(today(), cint(v.service_interval_months) or 6),
		"next_service_km": km + (cint(v.service_interval_km) or 5000),
		"reminder_sent_on": None,
	}
	frappe.db.set_value("Garage Vehicle", v.name, values)


def customer_phone(vehicle) -> str | None:
	phone = frappe.db.get_value("Customer", vehicle.customer, "mobile_no") if vehicle.customer else None
	if not phone and vehicle.last_check_in:
		phone = frappe.db.get_value("Vehicle Check In", vehicle.last_check_in, "contact_phone")
	return phone


def send_service_reminders():
	"""Daily: remind customers whose service is due within the next 7 days."""
	due = frappe.get_all(
		"Garage Vehicle",
		filters={"next_service_date": ("<=", add_days(today(), 7)), "reminder_sent_on": ("is", "not set")},
		pluck="name",
	)
	for name in due:
		v = frappe.get_doc("Garage Vehicle", name)
		message = _("Hello {0}, your {1} ({2}) is due for service on {3}. Reply or call us to book.").format(
			(v.customer_name or "").split(" ")[0] or _("customer"),
			v.description or v.make or _("vehicle"),
			v.name,
			frappe.utils.formatdate(getdate(v.next_service_date), "dd MMM"),
		)
		phone = customer_phone(v)
		if phone:
			from garage.sms import send_sms

			send_sms(phone, message, reference_doctype="Garage Vehicle", reference_name=v.name)
		v.add_comment("Info", _("Service reminder: {0}").format(message))
		frappe.db.set_value("Garage Vehicle", v.name, "reminder_sent_on", today())
	frappe.db.commit()
