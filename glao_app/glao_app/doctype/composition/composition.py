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

		amended_from: DF.Link | None
		items: DF.Table[CompositionItems]
		nomenclature: DF.Link | None
		not_available: DF.Check
		place: DF.Link | None
		project: DF.Link | None
	# end: auto-generated types

	def autoname(self):
		self.name = make_autoname(str(self.nomenclature) + "-.##.")

	def on_submit(self):
		return 0

	# def validate(self):
	#   self._link_stocks()

	def on_trash(self):
		self._unlink_stocks()

	def _link_stocks(self):
		for row in self.items:
			stock = frappe.get_all("Stock", filters=[["name", "=", row.item]], limit=1)
			doc = frappe.get_doc("Stock", str(stock[0].name), for_update=True)
			frappe.msgprint(str(row.item))
			#
			row.saved_place = doc.place_table[0].place
			if stock:
				doc = frappe.get_doc("Stock", str(stock[0].name), for_update=True)
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

				if doc.is_referenced:
					frappe.db.set_value("Stock", stock[0].name, "composition", self.name)
					ps_doc = frappe.get_doc("Places Stock", ps[0].name, for_update=True)
					ps_doc.delete()
					frappe.db.set_value("Stock", stock[0].name, "quantity", 0)
					# doc.save(ignore_permissions=True)
				else:
					ps_doc = frappe.get_doc("Places Stock", ps[0].name, for_update=True)
					row_qty = ps_doc.quantity - row.quantity
					place_to_save = ps_doc.place
					ps_doc.delete()
					doc.append(
						"place_table",
						{
							"doctype": "Places Stock",
							"place": place_to_save,
							"quantity": row_qty,
							"article": doc.article,
						},
					)
					doc.save(ignore_permissions=True)
					doc = frappe.get_doc("Stock", str(stock[0].name), for_update=True)
					end_qty = sum(row.quantity if row else 0 for row in doc.place_table)
					doc.quantity = end_qty
					doc.save(ignore_permissions=True)
					# frappe.throw(str(doc.quantity))
			else:
				frappe.throw(f"Stock introuvable : {row.item}")

	def _unlink_stocks(self):
		for row in self.items:
			# frappe.msgprint(str(row.item))
			stock = frappe.get_all("Stock", filters=[["name", "=", row.item]], limit=1)
			if stock:
				doc = frappe.get_doc("Stock", str(stock[0].name), for_update=True)
				frappe.msgprint(str(row.item))
				if doc.is_referenced:
					frappe.db.set_value("Stock", stock[0].name, "composition", None)
					doc.append(
						"place_table",
						{
							"doctype": "Places Stock",
							"place": row.saved_place,
							"quantity": 1,
							"article": doc.article,
						},
					).insert()
					frappe.db.set_value("Stock", stock[0].name, "quantity", 1)
				else:
					frappe.msgprint("Doit n'apparaitre qu'une fois")
					# if not row.saved_place:
					# frappe.throw(f"Pas de saved_place défini sur le stock {doc.name}")
					ps = frappe.get_all(
						"Places Stock",
						filters=[["parent", "=", doc.name], ["place", "=", row.saved_place]],
						fields=["name", "quantity"],
						limit=1,
					)
					# frappe.throw(str(ps))
					if ps:
						# delete and replace with the right quantity
						ps_doc = frappe.get_doc("Places Stock", ps[0].name, for_update=True)
						row_qty = ps_doc.quantity + row.quantity
						# frappe.throw(str(row_qty))
						ps_doc.delete()
						doc.save(ignore_permissions=True)
						doc.append(
							"place_table",
							{
								"doctype": "Places Stock",
								"place": row.saved_place,
								"quantity": row_qty,
								"article": doc.article,
							},
						)
						doc.save(ignore_permissions=True)
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
					doc = frappe.get_doc("Stock", str(stock[0].name), for_update=True)
					doc.composition = None
					doc.place_saved = None
					end_qty = sum(row.quantity if row else 0 for row in doc.place_table)
					doc.quantity = end_qty
					doc.save(ignore_permissions=True)
			else:
				frappe.throw("ah bon")
