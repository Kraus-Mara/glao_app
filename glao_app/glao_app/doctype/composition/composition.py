# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt
from operator import add
import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class Composition(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.composition_items.composition_items import CompositionItems

		items: DF.Table[CompositionItems]
		nomenclature: DF.Link | None
	# end: auto-generated types

	def autoname(self):
		self.name = make_autoname(str(self.nomenclature) + "-.##.")

	def validate(self):
		self._link_stocks()

	def on_trash(self):
		self._unlink_stocks()

	def _link_stocks(self):
		for row in self.items:
			stock = frappe.get_all("Stock", filters=[["name", "=", row.item]], limit=1)
			if stock:
				doc = frappe.get_doc("Stock", str(stock[0].name), for_update=True)
				if doc.is_referenced:
					frappe.db.set_value("Stock", stock[0].name, "composition", self.name)
				else:
					ps = frappe.get_all(
						"Places Stock",
						filters=[["parent", "=", doc.name]],
						fields=["name", "quantity"],
						limit=1,
					)
					if not ps:
						frappe.throw(f"Aucun Places Stock trouvé pour {doc.name} à {doc.place_saved}")
					if ps[0].quantity < row.quantity:
						frappe.throw(
							f"Stock insuffisant pour {doc.name} : {ps[0].quantity} disponible, {row.quantity} requis"
						)
					ps_doc = frappe.get_doc("Places Stock", ps[0].name, for_update=True)
					row_qty = ps_doc.quantity - row.quantity
					# frappe.throw(str(row_qty))  # Le bon chiffre
					place_to_save = ps_doc.place
					ps_doc.delete()
					# frappe.throw(str(doc.place_table))
					# working
					doc.append(
						"place_table",
						{
							"doctype": "Places Stock",
							"place": place_to_save,
							"quantity": row_qty,
							"article": doc.article,
						},
					)
					doc.place_saved = ps_doc.place
					doc.save(ignore_permissions=True)
					##
					doc = frappe.get_doc("Stock", str(stock[0].name), for_update=True)
					end_qty = sum(row.quantity for row in doc.place_table) if doc.place_table else 0
					doc.quantity = end_qty
					# frappe.throw(str(doc.quantity))
			else:
				frappe.throw(f"Stock introuvable : {row.item}")

	def _unlink_stocks(self):
		for row in self.items:
			stock = frappe.get_all("Stock", filters=[["name", "=", row.item]], limit=1)
			if stock:
				doc = frappe.get_doc("Stock", str(stock[0].name), for_update=True)
				if doc.is_referenced:
					frappe.db.set_value("Stock", stock[0].name, "composition", None)
				else:
					if not doc.place_saved:
						frappe.throw(f"Pas de place_saved défini sur le stock {doc.name}")
					ps = frappe.get_all(
						"Places Stock",
						filters=[["parent", "=", doc.name], ["place", "=", doc.place_saved]],
						fields=["name", "quantity"],
						limit=1,
					)
					if ps:
						ps_doc = frappe.get_doc("Places Stock", ps[0].name, for_update=True)
						row_qty = ps_doc.quantity + row.quantity
						ps_doc.quantity = row_qty
						ps_doc.save(ignore_permissions=True)
					else:
						doc.append(
							"place_table",
							{
								"doctype": "Places Stock",
								"place": doc.place_saved,
								"quantity": row.quantity,
								"article": doc.article,
							},
						)
					doc.composition = None
					doc.place_saved = None
					end_qty = sum(row.quantity for row in doc.place_table)
					doc.quantity = end_qty
					doc.save(ignore_permissions=True)
			else:
				frappe.throw("ah bon")
