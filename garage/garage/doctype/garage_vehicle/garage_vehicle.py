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
