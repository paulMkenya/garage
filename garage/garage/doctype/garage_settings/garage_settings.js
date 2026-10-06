frappe.ui.form.on("Garage Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Send Test SMS"), () => {
			frappe.prompt({ fieldname: "phone", fieldtype: "Data", label: __("Phone"), reqd: 1 }, (v) =>
				frappe.call("garage.sms.send_test_sms", { phone: v.phone }).then((r) =>
					frappe.set_route("Form", "Garage SMS Log", r.message)
				)
			);
		});
		frm.add_custom_button(__("SMS Log"), () => frappe.set_route("List", "Garage SMS Log"));
	},
});
