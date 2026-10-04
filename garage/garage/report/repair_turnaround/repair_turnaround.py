# Copyright (c) 2026, Cloudtrade and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, time_diff_in_hours


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = [
		{"label": _("Repair Order"), "fieldname": "name", "fieldtype": "Link", "options": "Repair Order", "width": 130},
		{"label": _("Plate"), "fieldname": "vehicle", "fieldtype": "Link", "options": "Garage Vehicle", "width": 100},
		{"label": _("Service Type"), "fieldname": "service_type", "width": 130},
		{"label": _("Technician"), "fieldname": "technician_name", "width": 130},
		{"label": _("Status"), "fieldname": "status", "width": 120},
		{"label": _("Received"), "fieldname": "received_on", "fieldtype": "Datetime", "width": 150},
		{"label": _("Wait To Start (h)"), "fieldname": "wait_hours", "fieldtype": "Float", "precision": 1, "width": 110},
		{"label": _("Work Time (h)"), "fieldname": "work_hours", "fieldtype": "Float", "precision": 1, "width": 100},
		{"label": _("Ready → Released (h)"), "fieldname": "collect_hours", "fieldtype": "Float", "precision": 1, "width": 130},
		{"label": _("Total In Garage (h)"), "fieldname": "total_hours", "fieldtype": "Float", "precision": 1, "width": 120},
		{"label": _("Promised Met"), "fieldname": "on_time", "width": 100},
	]
	conditions = {"docstatus": ("<", 2), "status": ("!=", "Cancelled")}
	if filters.from_date and filters.to_date:
		conditions["received_on"] = ("between", [filters.from_date, filters.to_date + " 23:59:59"])
	if filters.technician:
		conditions["technician"] = filters.technician
	rows = frappe.get_all(
		"Repair Order",
		filters=conditions,
		fields=["name", "vehicle", "service_type", "technician_name", "status", "received_on", "started_on",
			"completed_on", "promised_time"],
		order_by="received_on desc",
	)
	released = dict(
		frappe.get_all(
			"Gate Pass",
			filters={"docstatus": 1, "repair_order": ("in", [r.name for r in rows] or [""])},
			fields=["repair_order", "released_on"],
			as_list=True,
		)
	)
	def hours(a, b):
		return flt(time_diff_in_hours(b, a), 1) if a and b else None

	for r in rows:
		r.released_on = released.get(r.name)
		r.wait_hours = hours(r.received_on, r.started_on)
		r.work_hours = hours(r.started_on, r.completed_on)
		r.collect_hours = hours(r.completed_on, r.released_on)
		r.total_hours = hours(r.received_on, r.released_on)
		if r.promised_time and r.completed_on:
			r.on_time = _("Yes") if r.completed_on <= r.promised_time else _("No")
	done = [r for r in rows if r.total_hours is not None]
	avg = lambda key: flt(sum(r[key] or 0 for r in rows) / max(1, sum(1 for r in rows if r[key] is not None)), 1)
	summary = [
		{"label": _("Jobs"), "value": len(rows), "indicator": "Blue"},
		{"label": _("Released"), "value": len(done), "indicator": "Green"},
		{"label": _("Avg Wait To Start (h)"), "value": avg("wait_hours"), "indicator": "Orange"},
		{"label": _("Avg Work Time (h)"), "value": avg("work_hours"), "indicator": "Blue"},
		{"label": _("Avg Total In Garage (h)"), "value": avg("total_hours"), "indicator": "Purple"},
	]
	return columns, rows, None, None, summary
