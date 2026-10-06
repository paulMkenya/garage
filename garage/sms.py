"""Customer SMS via the Uwazii Mobile HTTP API (POST {base}/sms/1/text/single, Basic auth)."""

import re

import frappe
import requests
from frappe import _
from frappe.utils import flt, fmt_money, now_datetime

STATUS_SENT_GROUPS = {"PENDING", "DELIVERED"}


def normalize_phone(phone: str | None) -> str | None:
	digits = re.sub(r"\D", "", phone or "")
	if digits.startswith("0") and len(digits) == 10:
		digits = "254" + digits[1:]
	elif len(digits) == 9 and digits[0] in "17":
		digits = "254" + digits
	return digits if len(digits) >= 11 else None


def send_sms(phone, message, event=None, reference_doctype=None, reference_name=None):
	"""Log an SMS and queue it for sending. Returns the Garage SMS Log name."""
	settings = frappe.get_cached_doc("Garage Settings")
	number = normalize_phone(phone)
	if not number:
		return None
	log = frappe.get_doc(
		{
			"doctype": "Garage SMS Log",
			"phone": number,
			"event": event,
			"message": message,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"status": "Queued" if settings.sms_enabled else "Not Sent (SMS Disabled)",
		}
	).insert(ignore_permissions=True)
	if settings.sms_enabled:
		frappe.enqueue(
			"garage.sms.deliver", log_name=log.name, queue="short", enqueue_after_commit=True
		)
	return log.name


def deliver(log_name):
	log = frappe.get_doc("Garage SMS Log", log_name)
	settings = frappe.get_doc("Garage Settings")
	try:
		resp = requests.post(
			settings.sms_api_url.rstrip("/") + "/sms/1/text/single",
			json={"from": settings.sms_sender_id, "to": log.phone, "text": log.message},
			auth=(settings.sms_username, settings.get_password("sms_password")),
			headers={"Accept": "application/json"},
			timeout=20,
		)
		log.response = resp.text[:5000]
		msg = (resp.json().get("messages") or [{}])[0] if resp.ok else {}
		group = (msg.get("status") or {}).get("groupName")
		log.message_id = msg.get("messageId")
		log.status = "Sent" if resp.ok and group in STATUS_SENT_GROUPS else "Failed"
	except Exception as e:  # noqa: BLE001 - any send failure is logged, never raised
		log.status = "Failed"
		log.response = str(e)[:5000]
	log.sent_on = now_datetime()
	log.save(ignore_permissions=True)
	frappe.db.commit()


def _enabled(flag):
	return frappe.db.get_single_value("Garage Settings", flag)


def _first_name(name):
	return (name or "").split(" ")[0] or _("customer")


def _sign_off():
	company = frappe.defaults.get_defaults().get("company") or ""
	phone = frappe.db.get_single_value("Garage Settings", "garage_phone")
	return " - " + company + (f" {phone}" if phone else "")


def _link(ro):
	from garage.garage.doctype.repair_order.repair_order import customer_link

	return customer_link(ro)


def on_check_in_submit(doc, method=None):
	if not _enabled("sms_on_check_in"):
		return
	msg = _("Hi {0}, we have received your car {1} at the gate (ref {2}). We will update you on progress.").format(
		_first_name(doc.customer_name), doc.vehicle, doc.name
	)
	send_sms(doc.contact_phone, msg + _sign_off(), "Car Received", doc.doctype, doc.name)


def on_repair_order_update(doc, method=None):
	if not doc.has_value_changed("status"):
		return
	if doc.status == "Awaiting Approval" and _enabled("sms_on_estimate"):
		msg = _("Hi {0}, the estimate for {1} is {2}. View and approve: {3}").format(
			_first_name(doc.customer_name),
			doc.vehicle,
			fmt_money(flt(doc.parts_total) + flt(doc.labour_total) + flt(doc.other_total), currency=doc.currency),
			_link(doc),
		)
		send_sms(doc.contact_phone, msg + _sign_off(), "Estimate Ready", doc.doctype, doc.name)
	elif doc.status == "Ready for Collection" and _enabled("sms_on_ready"):
		msg = _("Hi {0}, your car {1} is ready for collection. Details: {2}").format(
			_first_name(doc.customer_name), doc.vehicle, _link(doc)
		)
		send_sms(doc.contact_phone, msg + _sign_off(), "Car Ready", doc.doctype, doc.name)


def on_payment_submit(doc, method=None):
	if doc.payment_type != "Receive" or not _enabled("sms_on_payment"):
		return
	for ref in doc.references:
		if ref.reference_doctype != "Sales Invoice":
			continue
		ro = frappe.db.get_value("Sales Invoice", ref.reference_name, "repair_order")
		if not ro:
			continue
		ro = frappe.db.get_value("Repair Order", ro, ["name", "contact_phone", "customer_name", "vehicle"], as_dict=True)
		balance = frappe.db.get_value("Sales Invoice", ref.reference_name, "outstanding_amount")
		msg = _("Hi {0}, we have received {1} for {2}. Balance: {3}. Thank you.").format(
			_first_name(ro.customer_name),
			fmt_money(ref.allocated_amount, currency=doc.paid_from_account_currency),
			ro.vehicle,
			fmt_money(balance, currency=doc.paid_from_account_currency),
		)
		send_sms(ro.contact_phone, msg + _sign_off(), "Payment Received", doc.doctype, doc.name)


def on_gate_pass_submit(doc, method=None):
	if not _enabled("sms_on_release"):
		return
	phone = doc.collector_phone or frappe.db.get_value("Repair Order", doc.repair_order, "contact_phone")
	msg = _("Your car {0} was released at {1} to {2}. Thank you for choosing us.").format(
		doc.vehicle, frappe.utils.format_datetime(now_datetime(), "HH:mm"), doc.collected_by or _("you")
	)
	send_sms(phone, msg + _sign_off(), "Car Released", doc.doctype, doc.name)


@frappe.whitelist()
def send_test_sms(phone: str):
	frappe.only_for("System Manager")
	name = send_sms(phone, _("Test message from Garage"), "Test")
	if not name:
		frappe.throw(_("Invalid phone number"))
	return name
