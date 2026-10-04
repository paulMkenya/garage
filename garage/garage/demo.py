import frappe


def make_demo_data():
	"""Create a sample customer and vehicle for local testing (bench execute garage.garage.demo.make_demo_data)."""
	customer = frappe.db.get_value("Customer", {"customer_name": "John Kamau"})
	if not customer:
		customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": "John Kamau", "customer_type": "Individual"}
		).insert().name
	if not frappe.db.exists("Garage Vehicle", "KDA123A"):
		frappe.get_doc({
			"doctype": "Garage Vehicle", "license_plate": "kda 123a", "customer": customer, "make": "Toyota",
			"model": "Fielder", "year": 2015, "color": "Silver", "fuel_type": "Petrol",
			"transmission": "Automatic", "vin": "NZE1613012345", "body_type": "Station Wagon",
		}).insert()
	frappe.db.commit()
	return customer
