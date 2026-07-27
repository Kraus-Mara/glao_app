# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from glao_app.glao_app.doctype.ref_events.ref_events import RefEvents
from frappe.utils import add_to_date
from frappe.utils import date_diff
from frappe.utils import today


class Stock(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.article_place_rules.article_place_rules import ArticlePlaceRules
		from glao_app.glao_app.doctype.maintenance_book.maintenance_book import Maintenancebook
		from glao_app.glao_app.doctype.places_stock.places_stock import PlacesStock
		from glao_app.glao_app.doctype.ref_events.ref_events import RefEvents

		actif: DF.Check
		article: DF.Link | None
		batch_no: DF.Data | None
		carnet_de_maintenance: DF.Table[Maintenancebook]
		closest_event_date: DF.Date | None
		code_spie_tm: DF.Data | None
		composition: DF.Link | None
		designation: DF.Data | None
		events: DF.Table[RefEvents]
		is_referenced: DF.Check
		not_yet_registered: DF.Check
		periodicity: DF.Data | None
		place_rules: DF.Table[ArticlePlaceRules]
		place_table: DF.Table[PlacesStock]
		quantity: DF.Int
		quantity_in_spie_tm: DF.Int
		rebut: DF.Check
		ref_constructeur: DF.Data | None
		reserved_quantity: DF.Int
		serial_no: DF.Data | None
		total_expected: DF.Int
		total_maximum: DF.Int
		total_minimum: DF.Int
	# end: auto-generated types

	def autoname(self):
		if self.is_referenced and self.serial_no:
			self.name = str(self.article) + "-SN-" + str(self.serial_no)
		elif self.is_referenced and self.batch_no:
			self.name = str(self.article) + "-BN-" + str(self.batch_no)
		else:
			self.name = str(self.article)

	def validate(self):
		self._check_dates()
		self._count_stock_in_spie()

	def _count_stock_in_spie(self):
		if self.article:
			qty = sum(row.quantity for row in self.place_table if not getattr(row, "external", 0))
			self.quantity_in_spie_tm = qty

	def _check_dates(self):
		# list(self.events) prevents any issue from the modification of a self.events element during the process
		for row in list(self.events):
			if row.passed and not row.already_checked:
				if row.event == "VGP":
					if not self.periodicity:
						frappe.throw(frappe._("The periodicity is not assigned in the article document"))
					periodicity = int(str(self.periodicity))
					row.already_checked = 1
					self.append(
						"events",
						{
							"doctype": "Ref Events",
							"event": row.event,
							"event_date": add_to_date(row.event_date, days=periodicity),
							"passed": 0,
							"batch_no": row.batch_no,
						},
					).insert(ignore_permissions=True)
				if row.event in ["DLU", "End of life"]:
					self.rebut = 1
			# keep the closest event date then put it in self.closest_event_date
		for row in self.events:
			if not row.passed and row.event_date:
				if self.closest_event_date is None or date_diff(row.event_date, today()) < date_diff(
					self.closest_event_date, today()
				):
					self.closest_event_date = row.event_date

	@frappe.whitelist()
	def _fetch_place_rules(self):
		pr = frappe.get_all(
			"Place Rules",
			filters=[["article", "=", self.article], ["parenttype", "=", "Places"]],
			fields=["name", "parent", "minimum_quantity", "expected_quantity", "maximum_quantity"],
		)
		return pr

	pass
