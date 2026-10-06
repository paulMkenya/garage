frappe.query_reports["Garage Revenue"] = {
	filters: [
		{fieldname: "company", label: "Company", fieldtype: "Link", options: "Company", default: frappe.defaults.get_user_default('Company')},
		{fieldname: "from_date", label: "From Date", fieldtype: "Date", default: frappe.datetime.month_start(), reqd: 1},
		{fieldname: "to_date", label: "To Date", fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1},
		{fieldname: "group_by", label: "Group By", fieldtype: "Select", options: "Day\nMonth\nService Type\nTechnician", default: "Day"}
	],
};
