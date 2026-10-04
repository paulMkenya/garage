// Copyright (c) 2026, Cloudtrade and contributors
// For license information, please see license.txt

frappe.ui.form.on("Quality Check", {
	setup(frm) {
		frm.set_query("repair_order", () => ({ filters: { status: ["in", ["In Progress", "Quality Check"]] } }));
	},
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Mark unchecked as Pass"), () => {
				(frm.doc.items || []).forEach((r) => !r.result && frappe.model.set_value(r.doctype, r.name, "result", "Pass"));
			});
		}
		if (frm.doc.result) {
			frm.dashboard.set_headline_alert(
				frm.doc.result === "Pass"
					? __("Passed. Submitting marks the car Ready for Collection.")
					: __("Failed. Submitting sends the car back to In Progress."),
				frm.doc.result === "Pass" ? "green" : "red"
			);
		}
		if (frm.doc.repair_order) {
			frm.add_custom_button(__("Repair Order"), () => frappe.set_route("Form", "Repair Order", frm.doc.repair_order), __("View"));
		}
	},
});
