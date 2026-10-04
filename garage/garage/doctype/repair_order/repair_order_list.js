frappe.listview_settings["Repair Order"] = {
	add_fields: ["status"],
	get_indicator(doc) {
		const colours = {
			Received: "blue", Diagnosis: "purple", "Awaiting Approval": "orange", Approved: "cyan",
			"In Progress": "yellow", "Waiting for Parts": "red", "Quality Check": "pink",
			"Ready for Collection": "green", Released: "gray", Cancelled: "red",
		};
		return [__(doc.status), colours[doc.status] || "gray", "status,=," + doc.status];
	},
};
