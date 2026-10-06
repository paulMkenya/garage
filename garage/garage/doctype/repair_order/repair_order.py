# Copyright (c) 2026, Cloudtrade and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

RO_STATUSES = (
	"Received", "Diagnosis", "Awaiting Approval", "Approved", "In Progress", "Waiting for Parts",
	"Quality Check", "Ready for Collection", "Released", "Cancelled",
)
CHECK_IN_STATUS = {
	"Ready for Collection": "Ready for Collection",
	"Released": "Released",
}
WORKING = ("In Progress", "Waiting for Parts", "Quality Check")


class RepairOrder(Document):
	def validate(self):
		if not self.currency and self.company:
			self.currency = frappe.get_cached_value("Company", self.company, "default_currency")
		if self.vehicle and not self.vehicle_description:
			self.vehicle_description = frappe.get_doc("Garage Vehicle", self.vehicle).description
		if not self.customer_link_key:
			self.customer_link_key = frappe.generate_hash(length=24)
		self.set_item_defaults()
		self.calculate_totals()
		self.stamp_times()

	def set_item_defaults(self):
		price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list") or "Standard Selling"
		for row in self.items:
			item = frappe.get_cached_value(
				"Item", row.item_code, ["is_stock_item", "item_group", "stock_uom"], as_dict=True
			)
			if not row.item_type:
				row.item_type = "Part" if item.is_stock_item else "Labour"
			if not row.uom:
				row.uom = item.stock_uom
			if not flt(row.rate):
				row.rate = flt(
					frappe.db.get_value("Item Price", {"item_code": row.item_code, "price_list": price_list}, "price_list_rate")
				)
			row.amount = flt(row.qty) * flt(row.rate)

	def calculate_totals(self):
		totals = {"Part": 0, "Labour": 0}
		other = approved = 0
		for row in self.items:
			if row.item_type in totals:
				totals[row.item_type] += flt(row.amount)
			else:
				other += flt(row.amount)
			if row.approved:
				approved += flt(row.amount)
		self.parts_total = totals["Part"]
		self.labour_total = totals["Labour"]
		self.other_total = other
		self.approved_total = approved

	def stamp_times(self):
		if self.status in WORKING and not self.started_on:
			self.started_on = now_datetime()
		if self.status in ("Ready for Collection", "Released") and not self.completed_on:
			self.completed_on = now_datetime()
		if self.status in ("Quality Check", "Ready for Collection", "Released"):
			open_jobs = [j.concern for j in self.jobs if j.job_status in ("Pending", "In Progress") and j.approved]
			if open_jobs:
				frappe.throw(_("Finish or decline these approved jobs first: {0}").format(", ".join(open_jobs)))
		if (
			self.status == "Ready for Collection"
			and self.has_value_changed("status")
			and frappe.db.get_single_value("Garage Settings", "require_quality_check")
			and not self.has_passed_quality_check()
		):
			frappe.throw(_("Submit a passed Quality Check before marking the car Ready for Collection"))

	def has_passed_quality_check(self):
		return bool(
			self.quality_check
			and frappe.db.get_value("Quality Check", self.quality_check, ["docstatus", "result"]) == (1, "Pass")
		)

	def on_update(self):
		if self.check_in and self.has_value_changed("status"):
			frappe.db.set_value(
				"Vehicle Check In", self.check_in, "status", CHECK_IN_STATUS.get(self.status, "In Workshop")
			)

	def get_billable_items(self):
		return [row for row in self.items if row.approved]


def _sales_item(row, warehouse=None):
	return {
		"item_code": row.item_code,
		"item_name": row.item_name,
		"description": row.description or row.item_name,
		"qty": row.qty,
		"uom": row.uom,
		"rate": row.rate,
		"warehouse": row.warehouse or warehouse,
	}


@frappe.whitelist()
def make_quotation(repair_order: str):
	ro = frappe.get_doc("Repair Order", repair_order)
	ro.check_permission("write")
	if not ro.items:
		frappe.throw(_("Add parts and labour before creating an estimate"))
	q = frappe.new_doc("Quotation")
	q.quotation_to = "Customer"
	q.party_name = ro.customer
	q.company = ro.company
	q.repair_order = ro.name
	q.order_type = "Maintenance"
	for row in ro.items:
		q.append("items", _sales_item(row))
	q.insert()
	ro.quotation = q.name
	if ro.approval_status in (None, "", "Not Requested"):
		ro.approval_status = "Requested"
	if ro.status in ("Received", "Diagnosis"):
		ro.status = "Awaiting Approval"
	ro.save()
	return q.name


@frappe.whitelist()
def record_approval(repair_order: str, approved_by: str, method: str, approved_rows: str | list | None = None):
	ro = frappe.get_doc("Repair Order", repair_order)
	ro.check_permission("write")
	rows = frappe.parse_json(approved_rows) if approved_rows else [r.name for r in ro.items]
	return apply_approval(ro, approved_by, method, rows)


def apply_approval(ro, approved_by, method, rows):
	for row in ro.items:
		row.approved = 1 if row.name in rows else 0
	for job in ro.jobs:
		job.approved = 1 if job.job_status != "Declined" else 0
	approved = [r for r in ro.items if r.approved]
	ro.approval_status = (
		"Declined" if not approved else ("Approved" if len(approved) == len(ro.items) else "Partially Approved")
	)
	ro.approved_by = approved_by
	ro.approval_method = method
	ro.approved_on = now_datetime()
	if ro.status in ("Received", "Diagnosis", "Awaiting Approval") and approved:
		ro.status = "Approved"
	ro.save()
	ro.add_comment("Info", _("Customer approval recorded: {0} by {1} via {2}").format(ro.approval_status, approved_by, method))
	return ro.approval_status


def customer_link(ro) -> str:
	if not ro.customer_link_key:
		ro.db_set("customer_link_key", frappe.generate_hash(length=24))
	return frappe.utils.get_url("/car-status?key=" + ro.customer_link_key)


@frappe.whitelist()
def get_customer_link(repair_order: str):
	ro = frappe.get_doc("Repair Order", repair_order)
	ro.check_permission("read")
	return customer_link(ro)


@frappe.whitelist()
def make_sales_invoice(repair_order: str):
	ro = frappe.get_doc("Repair Order", repair_order)
	ro.check_permission("write")
	if ro.sales_invoice and frappe.db.get_value("Sales Invoice", ro.sales_invoice, "docstatus") != 2:
		return ro.sales_invoice
	items = ro.get_billable_items()
	if not items:
		frappe.throw(_("There are no approved parts or labour to invoice"))
	warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse")
	si = frappe.new_doc("Sales Invoice")
	si.customer = ro.customer
	si.company = ro.company
	si.repair_order = ro.name
	si.update_stock = 1 if any(frappe.get_cached_value("Item", r.item_code, "is_stock_item") for r in items) else 0
	if si.update_stock:
		si.set_warehouse = warehouse
	for row in items:
		si.append("items", _sales_item(row, warehouse))
	si.remarks = _("Repair Order {0} for {1}").format(ro.name, ro.vehicle)
	si.insert()
	ro.db_set("sales_invoice", si.name)
	return si.name


@frappe.whitelist()
def make_repair_order(check_in: str):
	ci = frappe.get_doc("Vehicle Check In", check_in)
	ci.check_permission("read")
	if ci.docstatus != 1:
		frappe.throw(_("Submit the check-in first"))
	existing = frappe.db.get_value("Repair Order", {"check_in": ci.name, "status": ("!=", "Cancelled")})
	if existing:
		return existing
	ro = frappe.new_doc("Repair Order")
	ro.update({
		"vehicle": ci.vehicle,
		"customer": ci.customer,
		"vehicle_description": ci.vehicle_description,
		"contact_phone": ci.contact_phone,
		"check_in": ci.name,
		"odometer": ci.odometer,
		"service_type": ci.service_type,
		"company": ci.company or frappe.defaults.get_user_default("Company"),
		"promised_time": ci.promised_time,
		"approval_limit": ci.approval_limit,
		"received_on": ci.check_in_time,
	})
	for c in ci.concerns:
		ro.append("jobs", {"concern": c.concern})
	ro.insert()
	ci.db_set("status", "In Workshop")
	return ro.name


def link_on_submit(doc, method=None):
	"""Quotation / Sales Invoice hooks: keep Repair Order in sync."""
	if not doc.get("repair_order") or not frappe.db.exists("Repair Order", doc.repair_order):
		return
	if doc.doctype == "Sales Invoice":
		frappe.db.set_value("Repair Order", doc.repair_order, "sales_invoice", doc.name)
