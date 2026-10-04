app_name = "garage"
app_title = "Garage"
app_publisher = "Cloudtrade"
app_description = "Garage / workshop management for ERPNext"
app_email = "webshippa@gmail.com"
app_license = "mit"
required_apps = ["erpnext"]

app_include_css = ["/assets/garage/css/garage.css"]

jinja = {"methods": ["garage.damage_map.damage_map_svg"]}

after_install = "garage.install.after_install"
after_migrate = ["garage.install.after_install"]

doc_events = {
	"Sales Invoice": {"on_submit": "garage.garage.doctype.repair_order.repair_order.link_on_submit"},
}

scheduler_events = {"daily": ["garage.reminders.send_service_reminders"]}
