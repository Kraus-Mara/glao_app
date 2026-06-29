# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Expedition(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		client: DF.Data | None
		delivery_date: DF.Date | None
		dmc: DF.Link | None
		job_no: DF.Data | None
		project: DF.Link | None
		status: DF.Literal["Waiting", "Shipped"]
	# end: auto-generated types

	pass

	def validate(self):
		if self.status == "Shipped":
			self._send_dmc()
		else:
			return 1

	def _send_dmc(self):
		"""transfers item to CLIENTS/SITE and substract this quantity in stock.reserved_quantity"""
		dmc_items = frappe.get_all("Gestion DMC Items", filters=[["parent", "=", self.dmc]])
		for d in dmc_items:
			if d.status not in ["Validated", "Partially Validated"]:
				continue
			for r in d:
				if r.reserved:
					frappe.new_doc(
						doctype="Movement",
						type="Transfert",
						article_from_stock=r.item_from_stock,
						quantity_to_manipulate=r.true_quantity,
						source_place=r.source_place,
						target_place="CLIENTS/" + str(r.client) + "/SITE",
					)
		dmc_compos = frappe.get_all("Gestion DMC Composition", filters=[["parent", "=", self.dmc]])
		for d in dmc_compos:
			for c in d:
				if c.comp_saved:
					frappe.db.set_value("Composition", c.composition, "not_available", 1)
					frappe.db.set_value(
						"Composition", c.composition, "place", "CLIENTS/" + str(c.client) + "/SITE"
					)
					frappe.db.set_value("Composition", c.composition, "reserved", 0)
		frappe.msgprint("Items and Compositions were send with success")
