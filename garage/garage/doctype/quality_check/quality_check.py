# Copyright (c) 2026, Cloudtrade and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from garage.setup_data import QC_CHECKS


class QualityCheck(Document):
	def validate(self):
		failed = [r.check_item for r in self.items if r.result == "Fail"]
		if self.road_test_result == "Done - Fail":
			failed.append(_("Road test"))
		self.result = "Fail" if failed else ("Pass" if all(r.result for r in self.items) else None)
		if self.road_test_end_km and cint(self.road_test_end_km) < cint(self.road_test_start_km):
			frappe.throw(_("Road test end odometer cannot be lower than the start"))

	def before_submit(self):
		errors = []
		if not self.items:
			errors.append(_("Add the checks to inspect"))
		unanswered = [r.check_item for r in self.items if not r.result]
		if unanswered:
			errors.append(_("Not checked yet: {0}").format(", ".join(unanswered)))
		if self.road_test_result != "Not Required":
			if not (self.road_test_start_km and self.road_test_end_km):
				errors.append(_("Enter the road test start and end odometer"))
			if not self.road_tested_by:
				errors.append(_("Enter who did the road test"))
		if self.result == "Fail" and not self.issues_found:
			errors.append(_("Describe the issues found"))
		if errors:
			frappe.throw("<br>".join("&bull; " + e for e in errors), title=_("Quality check is not complete"))

	def on_submit(self):
		ro = frappe.get_doc("Repair Order", self.repair_order)
		ro.quality_check = self.name
		ro.status = "Ready for Collection" if self.result == "Pass" else "In Progress"
		ro.flags.ignore_permissions = True
		ro.save()
		if self.result == "Fail":
			ro.add_comment("Info", _("Quality check {0} failed: {1}").format(self.name, self.issues_found))

	def on_cancel(self):
		ro = frappe.get_doc("Repair Order", self.repair_order)
		if ro.quality_check == self.name and ro.status == "Ready for Collection":
			ro.quality_check = None
			ro.status = "Quality Check"
			ro.flags.ignore_permissions = True
			ro.save()


@frappe.whitelist()
def make_quality_check(repair_order: str):
	ro = frappe.get_doc("Repair Order", repair_order)
	ro.check_permission("write")
	existing = frappe.db.get_value("Quality Check", {"repair_order": ro.name, "docstatus": 0})
	if existing:
		return existing
	if ro.status not in ("In Progress", "Quality Check"):
		frappe.throw(_("Start the work before the quality check (status is '{0}')").format(ro.status))
	if ro.status != "Quality Check":
		ro.status = "Quality Check"
		ro.save()
	qc = frappe.new_doc("Quality Check")
	qc.repair_order = ro.name
	for job in ro.jobs:
		if job.approved and job.job_status == "Done":
			qc.append("items", {"category": _("Job"), "check_item": (job.correction or job.concern)[:140]})
	for category, check in QC_CHECKS:
		qc.append("items", {"category": category, "check_item": check})
	qc.road_test_start_km = ro.odometer
	qc.road_tested_by = frappe.session.user
	qc.insert()
	return qc.name
