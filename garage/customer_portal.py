"""Public car-status page: customers see progress and approve the estimate with a secret link."""

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit

STEPS = ("Received", "Diagnosis", "Awaiting Approval", "Approved", "In Progress", "Quality Check", "Ready for Collection", "Released")
STEP_FOR = {"Waiting for Parts": "In Progress"}
CAN_APPROVE = ("Received", "Diagnosis", "Awaiting Approval")


def get_repair_order(key):
	if not key or len(key) < 20:
		return None
	name = frappe.db.get_value("Repair Order", {"customer_link_key": key})
	return frappe.get_doc("Repair Order", name) if name else None


def can_approve(ro):
	return ro.status in CAN_APPROVE and bool(ro.items) and ro.approval_status == "Requested"


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=60 * 10)
def respond_estimate(key: str, decision: str, approved_by: str, approved_rows: str | list | None = None):
	from garage.garage.doctype.repair_order.repair_order import apply_approval

	ro = get_repair_order(key)
	if not ro:
		frappe.throw(_("This link is not valid"), frappe.PermissionError)
	if not can_approve(ro):
		frappe.throw(_("This estimate has already been answered. Please call the garage to make changes."))
	approved_by = (approved_by or "").strip()[:140]
	if not approved_by:
		frappe.throw(_("Please enter your name"))
	rows = frappe.parse_json(approved_rows) if approved_rows else []
	if decision == "Decline":
		rows = []
	elif decision != "Approve" or not rows:
		frappe.throw(_("Tick at least one item to approve"))
	valid = {r.name for r in ro.items}
	rows = [r for r in rows if r in valid]
	ro.flags.ignore_permissions = True
	status = apply_approval(ro, approved_by, _("Online Link"), rows)
	return status
