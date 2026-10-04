# Copyright (c) 2026, Cloudtrade and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	group = filters.group_by or "Day"
	columns = [
		{"label": _(group), "fieldname": "period", "width": 140},
		{"label": _("Invoices"), "fieldname": "invoices", "fieldtype": "Int", "width": 80},
		{"label": _("Parts"), "fieldname": "parts", "fieldtype": "Currency", "width": 130},
		{"label": _("Labour"), "fieldname": "labour", "fieldtype": "Currency", "width": 130},
		{"label": _("Other"), "fieldname": "other", "fieldtype": "Currency", "width": 110},
		{"label": _("Invoiced (incl. tax)"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 150},
		{"label": _("Collected"), "fieldname": "collected", "fieldtype": "Currency", "width": 130},
		{"label": _("Outstanding"), "fieldname": "outstanding", "fieldtype": "Currency", "width": 130},
	]
	key = {
		"Day": "si.posting_date",
		"Month": "date_format(si.posting_date, '%%Y-%%m')",
		"Service Type": "ifnull(ro.service_type, 'Unspecified')",
		"Technician": "ifnull(ro.technician_name, 'Unassigned')",
	}[group]
	rows = frappe.db.sql(
		f"""
		select {key} as period, count(distinct si.name) as invoices,
			sum(si.grand_total) as grand_total, sum(si.outstanding_amount) as outstanding,
			sum(ro.parts_total) as parts, sum(ro.labour_total) as labour, sum(ro.other_total) as other
		from `tabSales Invoice` si join `tabRepair Order` ro on ro.name = si.repair_order
		where si.docstatus = 1 and si.is_return = 0 and si.posting_date between %(from_date)s and %(to_date)s
			and (%(company)s = '' or si.company = %(company)s)
		group by 1 order by 1
		""",
		{"from_date": filters.from_date, "to_date": filters.to_date, "company": filters.company or ""},
		as_dict=True,
	)
	for r in rows:
		r.period = str(r.period)
		r.collected = flt(r.grand_total) - flt(r.outstanding)
	total = lambda k: sum(flt(r[k]) for r in rows)
	summary = [
		{"label": _("Invoiced"), "value": total("grand_total"), "datatype": "Currency", "indicator": "Blue"},
		{"label": _("Collected"), "value": total("collected"), "datatype": "Currency", "indicator": "Green"},
		{"label": _("Outstanding"), "value": total("outstanding"), "datatype": "Currency", "indicator": "Red"},
		{"label": _("Parts"), "value": total("parts"), "datatype": "Currency", "indicator": "Grey"},
		{"label": _("Labour"), "value": total("labour"), "datatype": "Currency", "indicator": "Grey"},
	]
	chart = {
		"data": {"labels": [r.period for r in rows], "datasets": [
			{"name": _("Parts"), "values": [flt(r.parts) for r in rows]},
			{"name": _("Labour"), "values": [flt(r.labour) for r in rows]}]},
		"type": "bar", "barOptions": {"stacked": 1},
	}
	return columns, rows, None, chart, summary
