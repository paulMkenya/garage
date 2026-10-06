# Copyright (c) 2026, Cloudtrade and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, now_datetime, time_diff_in_hours

OPEN = ("Checked In", "In Workshop", "Ready for Collection")


def execute(filters=None):
	columns = [
		{"label": _("Check-In"), "fieldname": "check_in", "fieldtype": "Link", "options": "Vehicle Check In", "width": 140},
		{"label": _("Plate"), "fieldname": "vehicle", "fieldtype": "Link", "options": "Garage Vehicle", "width": 100},
		{"label": _("Vehicle"), "fieldname": "vehicle_description", "width": 180},
		{"label": _("Customer"), "fieldname": "customer_name", "width": 150},
		{"label": _("Phone"), "fieldname": "contact_phone", "width": 120},
		{"label": _("Checked In"), "fieldname": "check_in_time", "fieldtype": "Datetime", "width": 150},
		{"label": _("Days In Yard"), "fieldname": "days", "fieldtype": "Int", "width": 90},
		{"label": _("Repair Order"), "fieldname": "repair_order", "fieldtype": "Link", "options": "Repair Order", "width": 130},
		{"label": _("Job Status"), "fieldname": "ro_status", "width": 140},
		{"label": _("Technician"), "fieldname": "technician_name", "width": 130},
		{"label": _("Bay"), "fieldname": "bay", "width": 80},
		{"label": _("Promised"), "fieldname": "promised_time", "fieldtype": "Datetime", "width": 150},
		{"label": _("Overdue (h)"), "fieldname": "overdue_hours", "fieldtype": "Float", "precision": 1, "width": 90},
	]
	rows = frappe.db.sql(
		"""
		select ci.name as check_in, ci.vehicle, ci.vehicle_description, ci.customer_name, ci.contact_phone,
			ci.check_in_time, ci.status as ci_status, ro.name as repair_order, ro.status as ro_status,
			ro.technician_name, ro.bay, coalesce(ro.promised_time, ci.promised_time) as promised_time
		from `tabVehicle Check In` ci
		left join `tabRepair Order` ro on ro.check_in = ci.name and ro.status != 'Cancelled'
		where ci.docstatus = 1 and ci.status in %(open)s
		order by ci.check_in_time
		""",
		{"open": OPEN},
		as_dict=True,
	)
	now = now_datetime()
	for r in rows:
		r.days = date_diff(now, r.check_in_time)
		r.ro_status = r.ro_status or _("No Repair Order")
		if r.promised_time and r.promised_time < now and r.ro_status != "Ready for Collection":
			r.overdue_hours = time_diff_in_hours(now, r.promised_time)
	statuses = {}
	for r in rows:
		statuses[r.ro_status] = statuses.get(r.ro_status, 0) + 1
	chart = {
		"data": {"labels": list(statuses), "datasets": [{"name": _("Cars"), "values": list(statuses.values())}]},
		"type": "bar",
	}
	summary = [
		{"label": _("Cars In Yard"), "value": len(rows), "indicator": "Blue"},
		{"label": _("Ready For Collection"), "value": statuses.get("Ready for Collection", 0), "indicator": "Green"},
		{"label": _("Overdue"), "value": sum(1 for r in rows if r.overdue_hours), "indicator": "Red"},
	]
	return columns, rows, None, chart, summary
