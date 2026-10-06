# Copyright (c) 2026, Cloudtrade and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, now_datetime

EXIT_PHOTOS = ("photo_exit_front", "photo_exit_rear", "photo_exit_left", "photo_exit_right")


class GatePass(Document):
	def validate(self):
		ro = frappe.get_doc("Repair Order", self.repair_order)
		self.currency = ro.currency
		self.set_invoice_balance()
		if self.release_basis == "Paid":
			self.authorised_by = None
		if self.exit_odometer and cint(self.exit_odometer) < cint(self.entry_odometer):
			frappe.throw(_("Exit odometer cannot be lower than the check-in reading ({0} km)").format(self.entry_odometer))

	def set_invoice_balance(self):
		self.grand_total = self.outstanding_amount = 0
		if self.sales_invoice:
			si = frappe.db.get_value(
				"Sales Invoice", self.sales_invoice, ["docstatus", "grand_total", "outstanding_amount"], as_dict=True
			)
			if si and si.docstatus == 1:
				self.grand_total = si.grand_total
				self.outstanding_amount = si.outstanding_amount

	def before_submit(self):
		settings = frappe.get_cached_doc("Garage Settings")
		ro_status = frappe.db.get_value("Repair Order", self.repair_order, "status")
		errors = []
		if ro_status != "Ready for Collection":
			errors.append(_("Repair Order is '{0}', it must be 'Ready for Collection'").format(ro_status))
		if frappe.db.exists("Gate Pass", {"repair_order": self.repair_order, "docstatus": 1, "name": ("!=", self.name)}):
			errors.append(_("This vehicle already has a submitted gate pass"))

		if self.release_basis == "Paid":
			si = (
				frappe.db.get_value("Sales Invoice", self.sales_invoice, ["docstatus", "repair_order"], as_dict=True)
				if self.sales_invoice
				else None
			)
			if not si or si.docstatus != 1:
				errors.append(_("No submitted Sales Invoice. Invoice the job or choose another release basis"))
			elif si.repair_order != self.repair_order:
				errors.append(_("Sales Invoice {0} is not for Repair Order {1}").format(self.sales_invoice, self.repair_order))
			elif flt(self.outstanding_amount) > 0:
				errors.append(
					_("Balance of {0} is still due. Take payment or get credit authorised").format(
						frappe.format_value(self.outstanding_amount, {"fieldtype": "Currency", "options": self.currency})
					)
				)
		else:
			role = settings.credit_approver_role or "Accounts Manager"
			if role in frappe.get_roles():
				self.authorised_by = frappe.session.user
			else:
				errors.append(_("Only a user with the '{0}' role can release a car on {1}").format(role, _(self.release_basis)))

		if settings.require_exit_photos:
			missing = [self.meta.get_label(f) for f in EXIT_PHOTOS if not self.get(f)]
			if missing:
				errors.append(_("Exit photos missing: {0}").format(", ".join(missing)))
		if not self.keys_returned:
			errors.append(_("Confirm all keys / remotes were returned"))
		if settings.require_release_signature and not self.release_signature:
			errors.append(_("Customer release signature is missing"))
		if errors:
			frappe.throw("<br>".join("&bull; " + e for e in errors), title=_("Vehicle cannot be released yet"))
		self.released_by = frappe.session.user
		self.released_on = now_datetime()

	def on_submit(self):
		self._set_released("Released")
		if self.exit_odometer:
			frappe.db.set_value("Garage Vehicle", self.vehicle, "last_odometer", self.exit_odometer)
		from garage.reminders import update_service_due

		update_service_due(self)

	def on_cancel(self):
		self._set_released("Ready for Collection")

	def _set_released(self, status):
		ro = frappe.get_doc("Repair Order", self.repair_order)
		ro.status = status
		ro.flags.ignore_permissions = True
		ro.save()


@frappe.whitelist()
def make_gate_pass(repair_order: str):
	ro = frappe.get_doc("Repair Order", repair_order)
	ro.check_permission("read")
	existing = frappe.db.get_value("Gate Pass", {"repair_order": ro.name, "docstatus": ("<", 2)})
	if existing:
		return existing
	gp = frappe.new_doc("Gate Pass")
	gp.repair_order = ro.name
	gp.collected_by = ro.customer_name
	gp.collector_phone = ro.contact_phone
	gp.release_basis = "Paid" if ro.sales_invoice else "No Charge"
	for field in ("vehicle", "vehicle_description", "customer", "customer_name", "check_in", "company", "sales_invoice"):
		gp.set(field, ro.get(field))
	gp.entry_odometer = ro.odometer
	gp.flags.ignore_mandatory = True
	gp.insert()
	return gp.name
