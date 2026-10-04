// Copyright (c) 2026, Cloudtrade and contributors
// For license information, please see license.txt

const GARAGE_RO_METHOD = "garage.garage.doctype.repair_order.repair_order.";

frappe.ui.form.on("Repair Order", {
	setup(frm) {
		frm.set_query("item_code", "items", () => ({ filters: { disabled: 0, is_sales_item: 1 } }));
	},

	refresh(frm) {
		if (frm.is_new()) return;
		const next = {
			Received: ["Diagnosis"],
			Diagnosis: ["Awaiting Approval"],
			Approved: ["In Progress"],
			"In Progress": ["Waiting for Parts", "Quality Check"],
			"Waiting for Parts": ["In Progress"],
			"Quality Check": ["Ready for Collection", "In Progress"],
		}[frm.doc.status] || [];
		next.forEach((s) =>
			frm.add_custom_button(__(s), () => {
				frm.set_value("status", s);
				frm.save();
			}, __("Move to"))
		);

		if (!["Released", "Cancelled"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Estimate (Quotation)"), () => garage_ro_call(frm, "make_quotation", "Quotation"), __("Create"));
			frm.add_custom_button(__("Record Customer Approval"), () => garage_ro_approval(frm), __("Create"));
			if (frm.doc.approved_total) {
				frm.add_custom_button(__("Sales Invoice"), () => garage_ro_call(frm, "make_sales_invoice", "Sales Invoice"), __("Create"));
			}
		}
		if (frm.doc.status === "Ready for Collection") {
			frm.add_custom_button(__("Gate Pass"), async () => {
				if (frm.is_dirty()) await frm.save();
				const r = await frappe.call({
					method: "garage.garage.doctype.gate_pass.gate_pass.make_gate_pass",
					args: { repair_order: frm.doc.name }, freeze: true,
				});
				if (r.message) frappe.set_route("Form", "Gate Pass", r.message);
			}, __("Create"));
		}
		if (frm.doc.check_in) {
			frm.add_custom_button(__("Gate Check-In"), () => frappe.set_route("Form", "Vehicle Check In", frm.doc.check_in), __("View"));
		}
		if (frm.doc.approval_limit && frm.doc.approved_total > frm.doc.approval_limit && frm.doc.approval_status !== "Approved") {
			frm.dashboard.set_headline_alert(
				__("Total {0} is above the customer's approved limit {1}. Get approval before working.", [
					format_currency(frm.doc.approved_total, frm.doc.currency),
					format_currency(frm.doc.approval_limit, frm.doc.currency),
				]),
				"orange"
			);
		}
	},
});

frappe.ui.form.on("Repair Order Item", {
	qty: (frm, cdt, cdn) => garage_ro_amount(frm, cdt, cdn),
	rate: (frm, cdt, cdn) => garage_ro_amount(frm, cdt, cdn),
	async item_code(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.item_code) return;
		const item = await frappe.db.get_value("Item", row.item_code, ["is_stock_item", "stock_uom"]);
		frappe.model.set_value(cdt, cdn, "item_type", item.message.is_stock_item ? "Part" : "Labour");
		const price = await frappe.db.get_value("Item Price", { item_code: row.item_code, selling: 1 }, "price_list_rate");
		if (price.message && price.message.price_list_rate) {
			frappe.model.set_value(cdt, cdn, "rate", price.message.price_list_rate);
		}
	},
});

function garage_ro_amount(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	frappe.model.set_value(cdt, cdn, "amount", flt(row.qty) * flt(row.rate));
}

async function garage_ro_call(frm, method, doctype) {
	if (frm.is_dirty()) await frm.save();
	const r = await frappe.call({ method: GARAGE_RO_METHOD + method, args: { repair_order: frm.doc.name }, freeze: true });
	if (r.message) frappe.set_route("Form", doctype, r.message);
}

function garage_ro_approval(frm) {
	const d = new frappe.ui.Dialog({
		title: __("Record Customer Approval"),
		fields: [
			{ fieldname: "approved_by", fieldtype: "Data", label: __("Approved By"), reqd: 1, default: frm.doc.customer_name },
			{ fieldname: "method", fieldtype: "Select", label: __("How"), reqd: 1,
				options: "Phone Call\nIn Person\nSMS\nWhatsApp\nEmail", default: "Phone Call" },
			{ fieldname: "items_html", fieldtype: "HTML" },
		],
		primary_action_label: __("Save Approval"),
		async primary_action(values) {
			const rows = d.$wrapper.find("input.garage-approve:checked").map((i, el) => el.value).get();
			await frappe.call({ method: GARAGE_RO_METHOD + "record_approval", freeze: true,
				args: { repair_order: frm.doc.name, approved_by: values.approved_by, method: values.method,
					approved_rows: JSON.stringify(rows) } });
			d.hide();
			frm.reload_doc();
		},
	});
	d.fields_dict.items_html.$wrapper.html(
		(frm.doc.items || []).length
			? `<label class="control-label">${__("Approved items")}</label>` + frm.doc.items.map((r) => `
				<div class="checkbox"><label><input type="checkbox" class="garage-approve" value="${r.name}" ${r.approved ? "checked" : ""}>
				${frappe.utils.escape_html(r.item_name || r.item_code)} &middot; ${r.qty} &times; ${format_currency(r.rate, frm.doc.currency)}</label></div>`).join("")
			: `<p class="text-muted">${__("No parts or labour added yet")}</p>`
	);
	d.show();
}
