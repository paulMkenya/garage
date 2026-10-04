import frappe
from frappe import _

from garage.customer_portal import STEP_FOR, STEPS, can_approve, get_repair_order

no_cache = 1


def get_context(context):
	context.no_cache = 1
	context.show_sidebar = False
	ro = get_repair_order(frappe.form_dict.key)
	if not ro:
		frappe.local.response["http_status_code"] = 404
		context.invalid = True
		context.title = _("Link not valid")
		return context
	context.title = _("{0} status").format(ro.vehicle)
	context.ro = ro
	context.key = frappe.form_dict.key
	context.company = ro.company
	context.garage_phone = frappe.db.get_single_value("Garage Settings", "garage_phone")
	current = STEP_FOR.get(ro.status, ro.status)
	context.steps = [
		{"label": _(s), "state": "done" if STEPS.index(s) < STEPS.index(current) else ("current" if s == current else "todo")}
		for s in STEPS
	] if current in STEPS else []
	context.can_approve = can_approve(ro)
	context.total = sum((r.amount or 0) for r in ro.items)
	context.balance = None
	if ro.sales_invoice:
		si = frappe.db.get_value("Sales Invoice", ro.sales_invoice, ["docstatus", "outstanding_amount", "grand_total"], as_dict=True)
		if si and si.docstatus == 1:
			context.balance = si.outstanding_amount
			context.invoice_total = si.grand_total
	return context
