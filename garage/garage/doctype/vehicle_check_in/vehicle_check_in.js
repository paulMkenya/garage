// Copyright (c) 2026, Cloudtrade and contributors
// For license information, please see license.txt

const GARAGE_SEVERITY_COLOURS = { Minor: "#f5b301", Moderate: "#f07c00", Severe: "#d92d20" };
const GARAGE_FUEL_LEVELS = ["Empty", "Reserve", "1/4", "1/2", "3/4", "Full"];
let garage_car_svg = null;

function garage_view_for_point(x, y) {
	if (y < 240) return "Left Side";
	if (y > 470) return "Right Side";
	if (x < 200) return "Front";
	if (x > 1000) return "Rear";
	return "Top";
}

frappe.ui.form.on("Vehicle Check In", {
	setup(frm) {
		frm.set_query("template", () => ({ filters: {} }));
	},

	async onload(frm) {
		if (frm.is_new() && !frm.doc.template) {
			const settings = await frappe.db.get_doc("Garage Settings");
			if (settings.default_check_in_template) {
				frm.set_value("template", settings.default_check_in_template);
			}
			if (!frm.doc.terms && settings.check_in_terms) frm.set_value("terms", settings.check_in_terms);
		}
	},

	refresh(frm) {
		frm.trigger("render_damage_map");
		frm.trigger("render_fuel_gauge");
		frm.trigger("render_history");
		if (frm.doc.docstatus === 0 && (frm.doc.checklist || []).length) {
			frm.fields_dict.checklist.grid.add_custom_button(__("Mark all unanswered as OK"), () => {
				(frm.doc.checklist || []).forEach((row) => {
					if (!row.result) row.result = "OK";
				});
				frm.refresh_field("checklist");
				frm.dirty();
			});
		}
		if (frm.doc.docstatus === 1 && !["Released", "Cancelled"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Repair Order"), async () => {
				const r = await frappe.call({
					method: "garage.garage.doctype.repair_order.repair_order.make_repair_order",
					args: { check_in: frm.doc.name }, freeze: true,
				});
				if (r.message) frappe.set_route("Form", "Repair Order", r.message);
			}, __("Create"));
		}
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Print Check-In Receipt"), () =>
				frm.print_doc ? frm.print_doc() : frappe.set_route("print", frm.doctype, frm.doc.name)
			);
		}
	},

	vehicle(frm) {
		frm.trigger("render_history");
	},

	async template(frm) {
		if (!frm.doc.template || frm.doc.docstatus !== 0) return;
		if ((frm.doc.checklist || []).some((r) => r.result)) {
			const ok = await new Promise((resolve) =>
				frappe.confirm(__("Replace the checklist with the items from {0}?", [frm.doc.template]),
					() => resolve(true), () => resolve(false))
			);
			if (!ok) return;
		}
		const r = await frappe.call({
			method: "garage.garage.doctype.vehicle_check_in.vehicle_check_in.get_template_items",
			args: { template: frm.doc.template },
		});
		frm.clear_table("checklist");
		(r.message || []).forEach((item) => {
			frm.add_child("checklist", {
				category: item.category,
				check_item: item.check_item,
				result: item.default_result,
				help_text: item.help_text,
			});
		});
		frm.refresh_field("checklist");
		frm.refresh();
	},

	async render_history(frm) {
		const wrapper = frm.get_field("vehicle_history_html").$wrapper;
		wrapper.empty();
		if (!frm.doc.vehicle) return;
		const r = await frappe.call({
			method: "garage.garage.doctype.vehicle_check_in.vehicle_check_in.get_vehicle_summary",
			args: { vehicle: frm.doc.vehicle, exclude: frm.is_new() ? null : frm.doc.name },
		});
		const s = r.message;
		if (!s) return;
		if (s.description && frm.doc.docstatus === 0 && frm.doc.vehicle_description !== s.description) {
			frm.set_value("vehicle_description", s.description);
		}
		let html = `<div class="garage-history">`;
		if (s.open.length && frm.doc.docstatus === 0) {
			html += `<div class="alert alert-warning">${__("This vehicle is already in the yard")}: ${s.open
				.map((o) => `<a href="/app/vehicle-check-in/${o.name}">${o.name}</a>`)
				.join(", ")}</div>`;
		}
		html += `<div class="text-muted small">${__("Last odometer")}: <b>${
			s.last_odometer ? format_number(s.last_odometer, null, 0) + " km" : __("none")
		}</b> &middot; ${__("Previous visits")}: <b>${s.visits.length}</b></div>`;
		if (s.visits.length) {
			html += `<ul class="small" style="margin:4px 0 0 16px;padding:0">${s.visits
				.map((v) => `<li><a href="/app/vehicle-check-in/${v.name}">${v.name}</a> &middot; ${frappe.datetime.str_to_user(
					v.check_in_time)} &middot; ${frappe.utils.escape_html(v.service_type || "")} &middot; ${format_number(v.odometer, null, 0)} km</li>`)
				.join("")}</ul>`;
		}
		wrapper.html(html + "</div>");
	},

	fuel_level(frm) {
		frm.trigger("render_fuel_gauge");
	},

	render_fuel_gauge(frm) {
		const wrapper = frm.get_field("fuel_gauge_html").$wrapper;
		const editable = frm.doc.docstatus === 0;
		wrapper.html(`<div class="garage-fuel">${GARAGE_FUEL_LEVELS.map(
			(l, i) => `<button type="button" class="garage-fuel-step ${frm.doc.fuel_level === l ? "active" : ""} ${
				i < 2 ? "low" : ""}" data-level="${l}" ${editable ? "" : "disabled"}>${l}</button>`
		).join("")}</div>`);
		wrapper.find(".garage-fuel-step").on("click", function () {
			frm.set_value("fuel_level", $(this).data("level"));
		});
	},

	damage_marks_remove(frm) {
		frm.trigger("render_damage_map");
	},

	no_visible_damage(frm) {
		if (frm.doc.no_visible_damage && (frm.doc.damage_marks || []).length) {
			frappe.msgprint(__("Remove the damage marks first"));
			frm.set_value("no_visible_damage", 0);
		}
	},

	async render_damage_map(frm) {
		const wrapper = frm.get_field("damage_map_html").$wrapper;
		if (!garage_car_svg) {
			garage_car_svg = await (await fetch("/assets/garage/images/car_diagram.svg")).text();
		}
		const editable = frm.doc.docstatus === 0;
		wrapper.html(`
			<div class="garage-damage-map ${editable ? "editable" : ""}">${garage_car_svg}</div>
			<div class="garage-damage-legend small text-muted">
				${Object.entries(GARAGE_SEVERITY_COLOURS)
					.map(([k, c]) => `<span><i style="background:${c}"></i>${__(k)}</span>`)
					.join("")}
				${editable ? `<span>${__("Tap the car to add a mark. Tap a mark to edit it.")}</span>` : ""}
			</div>`);
		const svg = wrapper.find("svg")[0];
		const layer = svg.querySelector(".garage-marks");
		const NS = "http://www.w3.org/2000/svg";
		(frm.doc.damage_marks || []).forEach((m) => {
			const g = document.createElementNS(NS, "g");
			g.setAttribute("class", "garage-mark");
			g.dataset.name = m.name;
			const c = document.createElementNS(NS, "circle");
			c.setAttribute("cx", m.x);
			c.setAttribute("cy", m.y);
			c.setAttribute("r", 16);
			c.setAttribute("fill", GARAGE_SEVERITY_COLOURS[m.severity] || "#d92d20");
			c.setAttribute("stroke", "#fff");
			c.setAttribute("stroke-width", 3);
			const t = document.createElementNS(NS, "text");
			t.setAttribute("x", m.x);
			t.setAttribute("y", m.y + 6);
			t.setAttribute("text-anchor", "middle");
			t.setAttribute("font-size", 17);
			t.setAttribute("font-weight", 700);
			t.setAttribute("fill", "#fff");
			t.textContent = m.mark_no || m.idx;
			g.append(c, t);
			layer.append(g);
		});

		$(svg).on("click", (e) => {
			const mark_el = e.target.closest(".garage-mark");
			if (mark_el) {
				const row = (frm.doc.damage_marks || []).find((m) => m.name === mark_el.dataset.name);
				if (row) garage_mark_dialog(frm, row);
				return;
			}
			if (!editable) return;
			const pt = svg.createSVGPoint();
			pt.x = e.clientX;
			pt.y = e.clientY;
			const p = pt.matrixTransform(svg.getScreenCTM().inverse());
			garage_mark_dialog(frm, null, Math.round(p.x * 10) / 10, Math.round(p.y * 10) / 10);
		});
	},
});

function garage_mark_dialog(frm, row, x, y) {
	const editable = frm.doc.docstatus === 0;
	const view = row ? row.view : garage_view_for_point(x, y);
	const d = new frappe.ui.Dialog({
		title: row ? __("Damage mark #{0} ({1})", [row.mark_no || row.idx, __(view)]) : __("New damage mark ({0})", [__(view)]),
		fields: [
			{ fieldname: "damage_type", fieldtype: "Select", label: __("Damage"), reqd: 1,
				options: "Scratch\nDent\nCrack\nChip\nRust\nBroken\nMissing Part\nPaint Damage\nScuff\nOther",
				default: row ? row.damage_type : "Scratch", read_only: !editable },
			{ fieldname: "severity", fieldtype: "Select", label: __("Severity"), options: "Minor\nModerate\nSevere",
				default: row ? row.severity : "Minor", read_only: !editable },
			{ fieldname: "notes", fieldtype: "Small Text", label: __("Notes"), default: row ? row.notes : "",
				read_only: !editable },
			{ fieldname: "photo", fieldtype: "Attach Image", label: __("Photo"), default: row ? row.photo : "",
				read_only: !editable },
			{ fieldname: "photo_preview", fieldtype: "HTML",
				options: row && row.photo ? `<img src="${row.photo}" style="max-width:100%;border-radius:6px">` : "" },
		],
		primary_action_label: editable ? __("Save Mark") : __("Close"),
		primary_action(values) {
			if (!editable) return d.hide();
			if (row) {
				Object.assign(row, values);
				delete row.photo_preview;
			} else {
				frm.add_child("damage_marks", { view, x, y, damage_type: values.damage_type, severity: values.severity,
					notes: values.notes, photo: values.photo });
				frm.set_value("no_visible_damage", 0);
			}
			(frm.doc.damage_marks || []).forEach((m, i) => (m.mark_no = i + 1));
			frm.refresh_field("damage_marks");
			frm.dirty();
			frm.trigger("render_damage_map");
			d.hide();
		},
	});
	if (row && editable) {
		d.set_secondary_action_label(__("Delete Mark"));
		d.set_secondary_action(() => {
			frm.get_field("damage_marks").grid.grid_rows_by_docname[row.name].remove();
			(frm.doc.damage_marks || []).forEach((m, i) => (m.mark_no = i + 1));
			frm.refresh_field("damage_marks");
			frm.trigger("render_damage_map");
			d.hide();
		});
	}
	d.show();
}
