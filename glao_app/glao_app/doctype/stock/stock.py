# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from glao_app.glao_app.doctype.ref_events.ref_events import RefEvents
from frappe.utils import add_to_date


class Stock(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.maintenance_book.maintenance_book import Maintenancebook
		from glao_app.glao_app.doctype.places_stock.places_stock import PlacesStock
		from glao_app.glao_app.doctype.ref_events.ref_events import RefEvents

		article: DF.Link | None
		batch_no: DF.Data | None
		carnet_de_maintenance: DF.Table[Maintenancebook]
		code_spie_tm: DF.Data | None
		composition: DF.Link | None
		designation: DF.Data | None
		events: DF.Table[RefEvents]
		is_referenced: DF.Check
		not_yet_registered: DF.Check
		perime: DF.Check
		place_saved: DF.Link | None
		place_table: DF.Table[PlacesStock]
		quantity: DF.Int
		quantity_in_spie_tm: DF.Int
		ref_constructeur: DF.Data | None
		serial_no: DF.Data | None
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

	def _check_dates(self):
		for row in self.events:
			if row.passed and not row.already_checked:
				if row.event == "VGP":
					item_doc = frappe.get_doc(
						"Article",
						str(
							frappe.get_all(
								"Article", filters=[["manufacturer", "like", self.ref_constructeur]]
							)[0].name
						),
					)
					family = item_doc.group
					periodicity = frappe.get_doc("Articles Group", family).periodicity_in_days
					row.already_checked = 1
					assert row.already_checked == 1, "ça n'a pas fonctionné"
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
				if row.event == "DLU" or "End of life":
					self.perime = 1

	pass
