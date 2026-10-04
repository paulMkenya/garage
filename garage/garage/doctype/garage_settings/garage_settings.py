# Copyright (c) 2026, Cloudtrade and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class GarageSettings(Document):
	def validate(self):
		if self.sms_enabled:
			missing = [
				self.meta.get_label(f)
				for f in ("sms_api_url", "sms_username", "sms_password", "sms_sender_id")
				if not self.get(f)
			]
			if missing:
				frappe.throw(_("To enable SMS, fill in: {0}").format(", ".join(missing)))
