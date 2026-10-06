# Copyright (c) 2026, Cloudtrade and contributors
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document


def normalize_plate(plate: str | None) -> str:
	return re.sub(r"[^A-Z0-9]", "", (plate or "").upper())


class GarageVehicle(Document):
	def before_naming(self):
		self.license_plate = normalize_plate(self.license_plate)

	def validate(self):
		self.license_plate = normalize_plate(self.license_plate)
		if not self.license_plate:
			frappe.throw(frappe._("Number Plate is required"))
		if self.vin:
			self.vin = self.vin.strip().upper()

	@property
	def description(self):
		return " ".join(str(p) for p in (self.year, self.make, self.model, self.color) if p)


@frappe.whitelist()
def get_service_history(vehicle: str):
	frappe.has_permission("Garage Vehicle", "read", vehicle, throw=True)
	orders = frappe.get_all(
		"Repair Order",
		filters={"vehicle": vehicle},
		fields=["name", "received_on", "status", "odometer", "service_type", "approved_total", "currency",
			"technician_name", "sales_invoice", "check_in", "recommendations"],
		order_by="received_on desc",
		limit=50,
	)
	for ro in orders:
		ro.jobs = frappe.get_all(
			"Repair Order Job", filters={"parent": ro.name}, pluck="concern", order_by="idx"
		)
		ro.gate_pass = frappe.db.get_value("Gate Pass", {"repair_order": ro.name, "docstatus": 1})
	check_ins = frappe.get_all(
		"Vehicle Check In",
		filters={"vehicle": vehicle, "docstatus": 1, "name": ("not in", [o.check_in for o in orders if o.check_in] or [""])},
		fields=["name", "check_in_time", "status", "odometer"],
		order_by="check_in_time desc",
		limit=20,
	)
	return {"orders": orders, "check_ins": check_ins}
