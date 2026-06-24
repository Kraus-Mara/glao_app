# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Expedition(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		delivery_date: DF.Date | None
		dmc: DF.Link | None
		project: DF.Link | None
		status: DF.Literal["Waiting", "Shipped"]
	# end: auto-generated types

	pass

	# def _send_dmc(self):
	#   """Takes every items in CLIENTS/BOOK and call _transfer_item() to CLIENTS/SITE"""
	#   for row in self.gestion_items:
	#       if row.reserved:
	#           self._transfer_item(
	#               row, frappe.get_doc("Places", "CLIENTS/" + str(self.client) + "/SITE").name
	#           )
	#   for comp_row in self.compositions_de_dmc:
	#       if comp_row.comp_saved:
	#           self._composition_booking(
	#               comp_row, frappe.get_doc("Places", "CLIENTS/" + str(self.client) + "/SITE").name
	#           )
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
