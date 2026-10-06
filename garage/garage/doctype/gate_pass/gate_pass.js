// Copyright (c) 2026, Cloudtrade and contributors
// For license information, please see license.txt

frappe.ui.form.on("Gate Pass", {
	setup(frm) {
		frm.set_query("repair_order", () => ({ filters: { status: "Ready for Collection" } }));
	},
	refresh(frm) {
		if (frm.doc.docstatus === 0 && frm.doc.release_basis === "Paid" && frm.doc.outstanding_amount > 0) {
			frm.dashboard.set_headline_alert(
				__("Balance due: {0}. The car cannot leave until it is paid or credit is authorised.", [
					format_currency(frm.doc.outstanding_amount, frm.doc.currency),
				]),
				"red"
			);
			frm.add_custom_button(__("Take Payment"), () =>
				frappe.call({
					method: "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry",
					args: { dt: "Sales Invoice", dn: frm.doc.sales_invoice },
					callback(r) {
						const doc = frappe.model.sync(r.message)[0];
						frappe.set_route("Form", doc.doctype, doc.name);
					},
				})
			);
		}
		if (frm.doc.docstatus === 0 && !frm.is_new()) {
			frm.add_custom_button(__("Refresh Balance"), () => frm.save());
		}
	},
});
