# Copyright (c) 2026, Cloudtrade and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

OPEN_STATUSES = ("Checked In", "In Workshop", "Ready for Collection")
WALKAROUND_PHOTOS = ("photo_front", "photo_rear", "photo_left", "photo_right")
WARNING_LIGHTS = (
	"wl_check_engine", "wl_oil", "wl_battery", "wl_temperature", "wl_brake",
	"wl_abs", "wl_airbag", "wl_tpms", "wl_service", "wl_traction",
)


class VehicleCheckIn(Document):
	def validate(self):
		if self.docstatus == 0:
			self.status = "Draft"
		self.set_vehicle_description()
		if not self.terms:
			self.terms = frappe.db.get_single_value("Garage Settings", "check_in_terms")
		if self.odometer is not None and self.odometer < 0:
			frappe.throw(_("Odometer cannot be negative"))
		if self.wl_none and (self.wl_other or any(self.get(f) for f in WARNING_LIGHTS)):
			frappe.throw(_("Untick 'No warning lights' or clear the warning lights that are ticked"))
		for i, mark in enumerate(self.damage_marks, start=1):
			mark.mark_no = i
		if self.damage_marks:
			self.no_visible_damage = 0
		if self.belongings:
			self.no_valuables = 0

	def set_vehicle_description(self):
		if self.vehicle:
			v = frappe.db.get_value("Garage Vehicle", self.vehicle, ["year", "make", "model", "color"], as_dict=True)
			if v:
				self.vehicle_description = " ".join(str(p) for p in (v.year, v.make, v.model, v.color) if p)

	def before_submit(self):
		settings = frappe.get_cached_doc("Garage Settings")
		errors = []

		if settings.block_duplicate_check_in:
			open_ci = frappe.db.get_value(
				"Vehicle Check In",
				{"vehicle": self.vehicle, "docstatus": 1, "status": ("in", OPEN_STATUSES), "name": ("!=", self.name)},
			)
			if open_ci:
				errors.append(_("{0} is already in the yard on {1}").format(self.vehicle, open_ci))

		if settings.require_walkaround_photos:
			missing = [self.meta.get_label(f) for f in WALKAROUND_PHOTOS if not self.get(f)]
			if missing:
				errors.append(_("Walk-around photos missing: {0}").format(", ".join(missing)))
		if settings.require_dashboard_photo and not self.dashboard_photo:
			errors.append(_("Dashboard photo is missing"))
		if not (self.wl_none or self.wl_other or any(self.get(f) for f in WARNING_LIGHTS)):
			errors.append(_("Record the warning lights, or tick 'No warning lights'"))

		unanswered = [row.check_item for row in self.checklist if not row.result]
		if unanswered:
			errors.append(_("Checklist items without a result: {0}").format(", ".join(unanswered)))

		if not self.damage_marks and not self.no_visible_damage:
			errors.append(_("Mark the damage on the car diagram, or tick 'No visible body damage'"))
		if not self.belongings and not self.no_valuables:
			errors.append(_("List the belongings left in the vehicle, or tick that there are no valuables"))
		if not self.concerns:
			errors.append(_("Add at least one customer concern / request"))

		if settings.require_photo_for_damage:
			for row in self.checklist:
				if row.result == "Damaged" and not row.photo:
					errors.append(_("Photo needed for damaged item: {0}").format(row.check_item))
			for mark in self.damage_marks:
				if mark.severity == "Severe" and not mark.photo:
					errors.append(_("Photo needed for severe damage mark #{0}").format(mark.mark_no))

		if settings.require_customer_signature and not self.customer_signature:
			errors.append(_("Customer signature is missing"))

		if errors:
			frappe.throw("<br>".join(f"&bull; {e}" for e in errors), title=_("Check-in is not complete"))

		self.status = "Checked In"

	def on_submit(self):
		last = frappe.db.get_value("Garage Vehicle", self.vehicle, "last_odometer") or 0
		if self.odometer < last:
			frappe.msgprint(
				_("Odometer {0} km is lower than the last recorded {1} km").format(self.odometer, last),
				indicator="orange", alert=True,
			)
		frappe.db.set_value(
			"Garage Vehicle", self.vehicle,
			{"last_odometer": max(self.odometer, last), "last_check_in": self.name},
		)

	def on_cancel(self):
		self.db_set("status", "Cancelled")


@frappe.whitelist()
def get_template_items(template: str):
	frappe.has_permission("Vehicle Check In Template", "read", throw=True)
	return frappe.get_all(
		"Vehicle Check In Template Item",
		filters={"parent": template, "parenttype": "Vehicle Check In Template"},
		fields=["category", "check_item", "default_result", "help_text"],
		order_by="idx asc",
	)


@frappe.whitelist()
def get_vehicle_summary(vehicle: str, exclude: str | None = None):
	frappe.has_permission("Garage Vehicle", "read", vehicle, throw=True)
	v = frappe.get_doc("Garage Vehicle", vehicle)
	visits = frappe.get_all(
		"Vehicle Check In",
		filters={"vehicle": vehicle, "docstatus": 1, "name": ("!=", exclude or "")},
		fields=["name", "check_in_time", "odometer", "service_type", "status"],
		order_by="check_in_time desc",
		limit=5,
	)
	return {
		"description": v.description,
		"customer": v.customer,
		"last_odometer": v.last_odometer,
		"visits": visits,
		"open": [x for x in visits if x.status in OPEN_STATUSES],
	}
