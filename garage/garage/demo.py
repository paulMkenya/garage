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


DEMO_PARTS = [
	("PRT-OILFILTER-TOY", "Oil Filter (Toyota 90915-YZZE1)", "Nos", 850),
	("PRT-OIL-5W30", "Engine Oil 5W-30 (per litre)", "Litre", 1200),
	("PRT-AIRFILTER-NZE", "Air Filter (Fielder NZE161)", "Nos", 1800),
	("PRT-BRAKEPAD-F-NZE", "Front Brake Pads (Fielder)", "Nos", 4500),
	("PRT-SPARKPLUG", "Spark Plug (Denso)", "Nos", 950),
]
DEMO_LABOUR_RATES = {"LAB-GENERAL": 1500, "LAB-DIAG": 2500, "LAB-SERVICE": 2000, "LAB-ALIGN": 2500, "LAB-ROADTEST": 0}
DEMO_TECHNICIANS = ["Peter Otieno", "Mary Wanjiku"]


def make_demo_workshop():
	"""Demo parts with stock, labour prices and technicians (bench execute garage.garage.demo.make_demo_workshop)."""
	company = frappe.get_all("Company", limit=1, pluck="name")[0]
	warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse")
	for code, name, uom, rate in DEMO_PARTS:
		if not frappe.db.exists("Item", code):
			frappe.get_doc({
				"doctype": "Item", "item_code": code, "item_name": name, "item_group": "Garage Parts",
				"stock_uom": uom, "is_stock_item": 1, "valuation_rate": rate * 0.6,
			}).insert()
		_price(code, rate)
	for code, rate in DEMO_LABOUR_RATES.items():
		_price(code, rate)
	if not frappe.db.exists("Stock Entry", {"remarks": "Garage demo opening stock", "docstatus": 1}):
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Receipt"
		se.company = company
		se.remarks = "Garage demo opening stock"
		for code, _name, _uom, rate in DEMO_PARTS:
			se.append("items", {"item_code": code, "qty": 40, "t_warehouse": warehouse, "basic_rate": rate * 0.6})
		se.insert()
		se.submit()
	for full_name in DEMO_TECHNICIANS:
		first, last = full_name.split(" ", 1)
		if not frappe.db.exists("Employee", {"employee_name": full_name}):
			frappe.get_doc({
				"doctype": "Employee", "first_name": first, "last_name": last, "gender": "Male" if first == "Peter" else "Female",
				"date_of_birth": "1990-01-01", "date_of_joining": "2024-01-01", "company": company,
				"designation": None, "status": "Active",
			}).insert()
	frappe.db.commit()


def _price(item_code, rate):
	if not frappe.db.exists("Item Price", {"item_code": item_code, "price_list": "Standard Selling"}):
		frappe.get_doc({"doctype": "Item Price", "item_code": item_code, "price_list": "Standard Selling",
			"price_list_rate": rate}).insert()
