# Copyright (c) 2026, Cloudtrade and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

OPEN = ("Received", "Diagnosis", "Awaiting Approval", "Approved", "In Progress", "Waiting for Parts", "Quality Check")


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = [
		{"label": _("Technician"), "fieldname": "technician", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": _("Name"), "fieldname": "technician_name", "width": 160},
		{"label": _("Open Jobs"), "fieldname": "open_jobs", "fieldtype": "Int", "width": 90},
		{"label": _("In Progress"), "fieldname": "in_progress", "fieldtype": "Int", "width": 90},
		{"label": _("Jobs Done (period)"), "fieldname": "done_jobs", "fieldtype": "Int", "width": 120},
		{"label": _("Labour Hours (period)"), "fieldname": "labour_hours", "fieldtype": "Float", "precision": 1, "width": 130},
		{"label": _("Labour Value (period)"), "fieldname": "labour_value", "fieldtype": "Currency", "width": 140},
	]
	period = [filters.from_date or "1900-01-01", (filters.to_date or "2999-12-31") + " 23:59:59"]
	jobs = frappe.db.sql(
		"""
		select j.technician, ro.status as ro_status, j.job_status, ro.completed_on
		from `tabRepair Order Job` j join `tabRepair Order` ro on ro.name = j.parent
		where ifnull(j.technician, '') != '' and ro.status != 'Cancelled'
		""",
		as_dict=True,
	)
	labour = frappe.db.sql(
		"""
		select coalesce(nullif(i.technician, ''), ro.technician) as technician, sum(i.qty) as hours, sum(i.amount) as value
		from `tabRepair Order Item` i join `tabRepair Order` ro on ro.name = i.parent
		where i.item_type = 'Labour' and i.approved = 1 and ro.completed_on between %s and %s
		group by 1
		""",
		period,
		as_dict=True,
	)
	data = {}

	def row(tech):
		return data.setdefault(tech, frappe._dict(technician=tech, open_jobs=0, in_progress=0, done_jobs=0,
			labour_hours=0, labour_value=0))

	for j in jobs:
		r = row(j.technician)
		if j.ro_status in OPEN and j.job_status in ("Pending", "In Progress"):
			r.open_jobs += 1
			r.in_progress += j.job_status == "In Progress"
		elif j.job_status == "Done" and j.completed_on and period[0] <= str(j.completed_on) <= period[1]:
			r.done_jobs += 1
	for lab in labour:
		if lab.technician:
			r = row(lab.technician)
			r.labour_hours, r.labour_value = flt(lab.hours), flt(lab.value)
	names = dict(frappe.get_all("Employee", filters={"name": ("in", list(data) or [""])}, fields=["name", "employee_name"], as_list=True))
	rows = sorted(data.values(), key=lambda r: (-r.open_jobs, -r.labour_hours))
	for r in rows:
		r.technician_name = names.get(r.technician)
	chart = {
		"data": {
			"labels": [r.technician_name or r.technician for r in rows],
			"datasets": [{"name": _("Open Jobs"), "values": [r.open_jobs for r in rows]},
				{"name": _("Jobs Done"), "values": [r.done_jobs for r in rows]}],
		},
		"type": "bar",
	}
	return columns, rows, None, chart
