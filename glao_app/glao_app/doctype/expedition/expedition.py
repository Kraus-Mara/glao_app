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

	# def _get_all_from_project(self):
	#   all_dmc = frappe.get_all("Gestion DMC", filters=[["project", "=", self.project]])
	#   items = []
	#   compos = []
	#   for d in all_dmc:
	#       for r in frappe.get_all("Gestion DMC Items", filters=[["parent", "=", d]]):
	#           items.append([r.item_from_stock, r.designation, r.true_quantity]) if r.reserved else None
	#       for c in frappe.get_all("Gestion DMC Composition", filters=[["parent", "=", d]]):
	#           compos.append(c.composition) if c.quantity > 0 else None
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

	# def _expedier(self):
	#   if self.status != "Draft":
	#       items = []
	#       compos = []
	#       if self.gestion_items:
	#           for row in self.gestion_items:
	#               if row.reserved:
	#                   items.append({row.item_from_stock, row.true_quantity, row.source_place})
	#       if self.compositions_de_dmc:
	#           for r in self.compositions_de_dmc:
	#               if r.comp_saved:
	#                   compos.append({r.composition, r.place_saved})
