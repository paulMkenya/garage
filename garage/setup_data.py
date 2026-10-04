CHECK_IN_TERMS = """1. The vehicle is left at the owner's risk. The garage is not responsible for valuables not listed on this form.
2. The condition, damage, fuel level and odometer reading above were recorded together with the customer.
3. No extra work beyond the approved spend limit will be done without the customer's consent.
4. Vehicles not collected within 3 days of completion may attract a daily storage fee.
5. The vehicle will only be released against this receipt and payment (or approved credit)."""

STANDARD = [
	# Exterior body
	("Exterior", "Front bumper"),
	("Exterior", "Rear bumper"),
	("Exterior", "Bonnet / hood"),
	("Exterior", "Boot lid / tailgate"),
	("Exterior", "Roof"),
	("Exterior", "Front left fender / wing"),
	("Exterior", "Front right fender / wing"),
	("Exterior", "Left doors"),
	("Exterior", "Right doors"),
	("Exterior", "Left rear quarter panel"),
	("Exterior", "Right rear quarter panel"),
	("Exterior", "Side mirrors (both)"),
	("Exterior", "Number plates (front & rear)"),
	("Exterior", "Paint condition overall"),
	("Exterior", "Badges / emblems"),
	("Exterior", "Aerial / antenna"),
	("Exterior", "Mud flaps"),
	# Glass
	("Glass", "Windscreen", "Look for chips and cracks"),
	("Glass", "Rear window"),
	("Glass", "Side windows"),
	("Glass", "Wipers & washer"),
	# Lights
	("Lights", "Headlights (dip & main)"),
	("Lights", "Indicators / hazards"),
	("Lights", "Brake lights"),
	("Lights", "Tail & number plate lights"),
	("Lights", "Fog lights"),
	("Lights", "Reverse lights"),
	# Wheels & tyres
	("Wheels & Tyres", "Front left tyre", "Tread depth, sidewall cuts, bulges"),
	("Wheels & Tyres", "Front right tyre"),
	("Wheels & Tyres", "Rear left tyre"),
	("Wheels & Tyres", "Rear right tyre"),
	("Wheels & Tyres", "Spare wheel"),
	("Wheels & Tyres", "Rims / wheel caps"),
	("Wheels & Tyres", "Wheel nuts"),
	# Interior
	("Interior", "Seats & upholstery"),
	("Interior", "Dashboard & trims"),
	("Interior", "Carpets & floor mats"),
	("Interior", "Headliner / roof lining"),
	("Interior", "Seat belts"),
	("Interior", "Horn"),
	("Interior", "Air conditioning"),
	("Interior", "Radio / infotainment / screen"),
	("Interior", "Power windows"),
	("Interior", "Central locking / alarm"),
	("Interior", "Interior lights"),
	("Interior", "Rear-view mirror & sun visors"),
	("Interior", "Cleanliness / odour"),
	# Under the bonnet
	("Under the Bonnet", "Engine oil level"),
	("Under the Bonnet", "Coolant level"),
	("Under the Bonnet", "Brake fluid level"),
	("Under the Bonnet", "Battery condition"),
	("Under the Bonnet", "Visible leaks"),
	("Under the Bonnet", "Drive belts & hoses"),
	# Tools & safety equipment
	("Tools & Safety", "Jack"),
	("Tools & Safety", "Wheel spanner"),
	("Tools & Safety", "Warning triangles (x2)", "Required by NTSA"),
	("Tools & Safety", "Fire extinguisher", "Required by NTSA"),
	("Tools & Safety", "First aid kit"),
	("Tools & Safety", "Reflective jacket"),
	# Accessories
	("Accessories", "Car radio face / remote"),
	("Accessories", "Roof rack / roof bars"),
	("Accessories", "Tow bar"),
	("Accessories", "Dashcam / tracker"),
	("Accessories", "Phone charger / cables"),
]

QUICK = [
	("Exterior", "Body panels & bumpers"),
	("Exterior", "Side mirrors"),
	("Glass", "Windscreen & windows"),
	("Lights", "All lights working"),
	("Wheels & Tyres", "Tyres (all four)"),
	("Wheels & Tyres", "Spare wheel"),
	("Interior", "Seats & upholstery"),
	("Interior", "Dashboard & electrics"),
	("Interior", "Air conditioning"),
	("Interior", "Radio / screen"),
	("Tools & Safety", "Jack & wheel spanner"),
	("Tools & Safety", "Warning triangles (x2)"),
	("Tools & Safety", "Fire extinguisher"),
]

MOTORCYCLE = [
	("Body", "Fairings & panels"),
	("Body", "Fuel tank"),
	("Body", "Mirrors"),
	("Body", "Seat"),
	("Lights", "Headlight"),
	("Lights", "Indicators"),
	("Lights", "Brake / tail light"),
	("Wheels & Tyres", "Front tyre"),
	("Wheels & Tyres", "Rear tyre"),
	("Mechanical", "Chain & sprockets"),
	("Mechanical", "Brakes (front & rear)"),
	("Mechanical", "Horn"),
	("Accessories", "Helmet(s)"),
	("Accessories", "Top box / panniers"),
]

# name: (description, is_default, items)
TEMPLATES = {
	"Standard Check-In": ("Full walk-around check for cars, SUVs and pickups", 1, STANDARD),
	"Quick Check-In": ("Short check for quick services and regular customers", 0, QUICK),
	"Motorcycle Check-In": ("Check for motorcycles and boda bodas", 0, MOTORCYCLE),
}

LABOUR_ITEMS = [
	("LAB-GENERAL", "General Labour"),
	("LAB-DIAG", "Diagnosis / Fault Finding"),
	("LAB-SERVICE", "Service Labour"),
	("LAB-ELECTRICAL", "Electrical Labour"),
	("LAB-BODY", "Panel Beating & Paint Labour"),
	("LAB-ALIGN", "Wheel Alignment"),
	("LAB-BALANCE", "Wheel Balancing"),
	("LAB-AC", "AC Service Labour"),
	("LAB-ROADTEST", "Road Test"),
]

QC_CHECKS = [
	("Work", "All approved jobs completed"),
	("Work", "Old parts kept / bagged as the customer asked"),
	("Work", "No tools, rags or parts left in the car or engine bay"),
	("Fluids", "Engine oil level"),
	("Fluids", "Coolant level"),
	("Fluids", "Brake fluid level"),
	("Fluids", "No leaks under the car"),
	("Safety", "Wheel nuts torqued"),
	("Safety", "Tyre pressures set"),
	("Safety", "Brakes and handbrake"),
	("Safety", "Lights, indicators and horn"),
	("Electrical", "No warning lights on the dashboard"),
	("Electrical", "Service reminder reset"),
	("Finish", "Seat, mirror and radio settings restored"),
	("Finish", "Seat covers and floor mats removed"),
	("Finish", "No new damage compared with the check-in damage map"),
	("Finish", "Car cleaned"),
]
