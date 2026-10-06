frappe.query_reports["Repair Turnaround"] = {
	filters: [
		{fieldname: "from_date", label: "From Date", fieldtype: "Date", default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)},
		{fieldname: "to_date", label: "To Date", fieldtype: "Date", default: frappe.datetime.get_today()},
		{fieldname: "technician", label: "Technician", fieldtype: "Link", options: "Employee"}
	],
};
