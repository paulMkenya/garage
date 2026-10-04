# Copyright (c) 2026, Cloudtrade and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VehicleCheckInTemplate(Document):
	def on_update(self):
		if self.is_default:
			frappe.db.sql(
				"update `tabVehicle Check In Template` set is_default = 0 where name != %s", self.name
			)
