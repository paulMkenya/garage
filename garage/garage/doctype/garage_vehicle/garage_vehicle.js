// Copyright (c) 2026, Cloudtrade and contributors
// For license information, please see license.txt

frappe.ui.form.on("Garage Vehicle", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("New Check-In"), () =>
			frappe.new_doc("Vehicle Check In", { vehicle: frm.doc.name })
		);
		const due = frm.doc.next_service_date && frm.doc.next_service_date <= frappe.datetime.get_today();
		const km_due = frm.doc.next_service_km && frm.doc.last_odometer >= frm.doc.next_service_km;
		if (due || km_due) {
			frm.dashboard.set_headline_alert(__("Service is due for this vehicle"), "orange");
		}
		garage_render_history(frm);
	},
});

async function garage_render_history(frm) {
	const wrapper = frm.fields_dict.service_history_html.$wrapper;
	wrapper.html(`<p class="text-muted">${__("Loading...")}</p>`);
	const { message: h } = await frappe.call({
		method: "garage.garage.doctype.garage_vehicle.garage_vehicle.get_service_history",
		args: { vehicle: frm.doc.name },
	});
	if (!h.orders.length && !h.check_ins.length) {
		wrapper.html(`<p class="text-muted">${__("No visits yet")}</p>`);
		return;
	}
	const esc = frappe.utils.escape_html;
	const link = (dt, name) => name ? `<a href="/app/${frappe.router.slug(dt)}/${encodeURIComponent(name)}">${esc(name)}</a>` : "";
	const rows = h.orders.map((o) => `
		<tr>
			<td>${frappe.datetime.str_to_user(o.received_on || "").split(" ")[0]}</td>
			<td>${link("Repair Order", o.name)}<br><small class="text-muted">${esc(o.service_type || "")}</small></td>
			<td>${o.odometer ? format_number(o.odometer, null, 0) + " km" : ""}</td>
			<td>${(o.jobs || []).map(esc).join("<br>")}${o.recommendations ? `<br><small class="text-warning">${__("Recommended")}: ${esc(o.recommendations)}</small>` : ""}</td>
			<td>${esc(o.technician_name || "")}</td>
			<td class="text-right">${format_currency(o.approved_total, o.currency)}</td>
			<td>${esc(o.status)}<br><small>${link("Sales Invoice", o.sales_invoice)} ${link("Gate Pass", o.gate_pass)}</small></td>
		</tr>`).join("");
	const extra = h.check_ins.map((c) => `
		<tr><td>${frappe.datetime.str_to_user(c.check_in_time || "").split(" ")[0]}</td><td>${link("Vehicle Check In", c.name)}</td>
		<td>${c.odometer ? format_number(c.odometer, null, 0) + " km" : ""}</td><td colspan="3" class="text-muted">${__("Check-in only")}</td><td>${esc(c.status)}</td></tr>`).join("");
	wrapper.html(`
		<table class="table table-bordered table-sm garage-history">
			<thead><tr><th>${__("Date")}</th><th>${__("Repair Order")}</th><th>${__("Odometer")}</th><th>${__("Work")}</th>
			<th>${__("Technician")}</th><th class="text-right">${__("Total")}</th><th>${__("Status")}</th></tr></thead>
			<tbody>${rows}${extra}</tbody>
		</table>`);
}
