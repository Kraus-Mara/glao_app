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

		by_dmc: DF.Link | None
		client: DF.Data | None
		complete: DF.Check
		items: DF.Table[CompositionItems]
		nomenclature: DF.Link | None
		not_available: DF.Check
		place: DF.Link
		project: DF.Link | None
		reserved: DF.Check
		saved: DF.Check
	# end: auto-generated types

	def autoname(self):
		self.name = make_autoname(str(self.nomenclature) + "-.##.")

	def validate(self):
		self._link_stocks()
		self._check_all()

	def _check_all(self):
		for row in self.items:
			# CAS 1 : C'est une ligne totalement nouvelle (ou qui n'avait pas été liée)
			if not row.saved_item and row.item and row.quantity > 0:
				stock = frappe.get_doc("Stock", row.item)

				# On cherche d'abord un emplacement qui a du stock disponible
				dispo = [d for d in stock.place_table if d.quantity >= row.quantity]
				if not dispo and stock.place_table:
					dispo = [d for d in stock.place_table if d.quantity > 0]

				# Si on trouve un emplacement avec du stock, on le prend, sinon on se rabat sur le premier ou celui de la compo
				if dispo:
					row.saved_place = dispo[0].place
				elif not row.saved_place:
					row.saved_place = stock.place_table[0].place if stock.place_table else self.place

				self._substract_stock(row.item, row.saved_place, row.quantity)
				row.saved_item = row.item
				row.saved_quantity = row.quantity

			# CAS 2 : L'article a été modifié/remplacé sur une ligne existante
			elif row.saved_item and row.saved_item != row.item:
				# On recrédite l'ancien
				self._add_stock(row.saved_item, row.saved_place, row.saved_quantity)
				# On déduit le nouveau
				row.saved_item = None
				row.saved_quantity = 0
				# Ce bloc va s'arrêter là, et au prochain save (ou en ré-exécutant la boucle),
				# il sera traité par le CAS 1. Pour faire propre, on peut l'exécuter directement :
				if row.item and row.quantity > 0:
					stock = frappe.get_doc("Stock", row.item)
					if not row.saved_place or row.saved_place not in [d.place for d in stock.place_table]:
						row.saved_place = stock.place_table[0].place if stock.place_table else self.place
					self._substract_stock(row.item, row.saved_place, row.quantity)
					row.saved_item = row.item
					row.saved_quantity = row.quantity

			# CAS 3 : L'article est le même, mais la quantité a changé
			elif row.saved_item and row.saved_quantity and row.saved_quantity != row.quantity:
				diff = row.quantity - row.saved_quantity
				if diff > 0:
					# On va chercher dynamiquement où prendre la différence
					stock = frappe.get_doc("Stock", row.saved_item)
					dispo = [
						d for d in stock.place_table if d.place == row.saved_place and d.quantity >= diff
					]

					# Si l'emplacement d'origine n'a plus assez de stock pour la rallonge, on cherche ailleurs
					if not dispo:
						dispo = [d for d in stock.place_table if d.quantity >= diff]
					if not dispo and stock.place_table:
						dispo = [d for d in stock.place_table if d.quantity > 0]

					emplacement_source = dispo[0].place if dispo else row.saved_place

					self._substract_stock(row.saved_item, emplacement_source, diff)
					row.saved_place = emplacement_source
				else:
					# Réduction de quantité : on recrédite l'emplacement d'origine
					self._add_stock(row.saved_item, row.saved_place, abs(diff))

				row.saved_quantity = row.quantity

	def _substract_stock(self, item_code, place_name, qty_to_remove):
		stock = frappe.get_doc("Stock", item_code, for_update=True)
		ps_items = [d for d in stock.place_table if d.place == place_name]
		if not ps_items:
			frappe.throw(f"Emplacement {place_name} introuvable pour l'article {item_code}")
		ps_row = ps_items[0]
		if ps_row.quantity < qty_to_remove:
			frappe.throw(
				f"Stock insuffisant à l'emplacement {place_name} pour {item_code} : {ps_row.quantity} disponible, {qty_to_remove} requis"
			)
		if stock.is_referenced:
			frappe.db.set_value("Stock", stock.name, "composition", self.name, update_modified=False)
			stock.remove(ps_row)
			stock.quantity = 0
		else:
			ps_row.quantity -= qty_to_remove
			if ps_row.quantity <= 0:
				stock.remove(ps_row)
		stock.quantity = sum(d.quantity for d in stock.place_table)
		stock.save(ignore_permissions=True)

	def _add_stock(self, item_code, place_name, qty_to_add):
		stock = frappe.get_doc("Stock", item_code, for_update=True)
		if stock.is_referenced:
			frappe.db.set_value("Stock", stock.name, "composition", None, update_modified=False)
			stock.quantity = 1
			stock.append(
				"place_table",
				{"doctype": "Places Stock", "place": place_name, "quantity": 1, "article": stock.article},
			)
		else:
			ps_items = [d for d in stock.place_table if d.place == place_name]
			if ps_items:
				ps_items[0].quantity += qty_to_add
			else:
				stock.append(
					"place_table",
					{
						"doctype": "Places Stock",
						"place": place_name,
						"quantity": qty_to_add,
						"article": stock.article,
					},
				)
		stock.quantity = sum(d.quantity for d in stock.place_table)
		stock.save(ignore_permissions=True)

	def _link_stocks(self):
		for row in self.items:
			if row.saved_item and row.saved_place and row.saved_quantity:
				continue
			if not row.item:
				continue
			stock_list = frappe.get_all("Stock", filters=[["name", "=", row.item]], limit=1)
			if not stock_list:
				frappe.throw(f"Stock introuvable : {row.item}")
			stock = frappe.get_doc("Stock", stock_list[0].name, for_update=True)
			if not stock.place_table:
				frappe.throw(f"Aucun Places Stock trouvé pour {stock.name}")
			if not row.saved_place:
				row.saved_place = stock.place_table[0].place
			self._substract_stock(row.item, row.saved_place, row.quantity)
			row.saved_item = row.item
			row.saved_quantity = row.quantity

	def on_trash(self):
		self._unlink_stocks()

	def _unlink_stocks(self):
		for row in self.items:
			if row.saved_item and row.saved_place and row.saved_quantity:
				self._add_stock(row.saved_item, row.saved_place, row.saved_quantity)

	@frappe.whitelist()
	def get_places_from_stock():
		return 0

	pass
