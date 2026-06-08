# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class GestionDMC(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.gestion_dmc_items.gestion_dmc_items import GestionDMCItems

		delivery_address: DF.Data | None
		dmc_items: DF.Link | None
		dmc_name: DF.Data | None
		gestion_items: DF.Table[GestionDMCItems]
		project: DF.Link | None
		status: DF.Literal["Untreated", "Validated", "Partially validated"]
	# end: auto-generated types

	@frappe.whitelist()
	def valider_dmc(self):
		"""
		Bouton custom : vérifie que chaque ligne a un item_from_stock,
		crée les Movement de type Pull, sauvegarde et met à jour le statut.
		"""
		self.save(ignore_permissions=True)

		all_linked = all(row.item_from_stock for row in self.gestion_items)
		any_linked = any(row.item_from_stock for row in self.gestion_items)

		if not any_linked:
			frappe.throw("Aucun article lié à un stock — veuillez renseigner les champs 'item_from_stock'.")

		errors = []
		for row in self.gestion_items:
			if not row.item_from_stock:
				continue
			try:
				self._pull_item(row)
			except Exception as e:
				errors.append(f"{row.article} : {str(e)}")

		if errors:
			frappe.throw("\n".join(errors), title="Erreurs lors du Pull")

		self.status = "Validated" if all_linked else "Partially validated"
		self.save(ignore_permissions=True)
		frappe.msgprint(f"DMC validée — statut : {self.status}", title="Confirmation")

	def _pull_item(self, row):
		"""Crée un Movement Pull pour une ligne GestionDMCItems."""
		stock_doc = frappe.get_doc("Stock", row.item_from_stock)
		is_referenced = stock_doc.is_referenced

		movement = frappe.get_doc(
			{
				"doctype": "Movement",
				"type": "Pull",
				"second": 1 if is_referenced else 0,
				"article_from_stock": row.item_from_stock,
				"article_name": stock_doc.article,
				"source_place": row.source_place,
				"quantity_to_manipulate": row.quantity,
				"serial": stock_doc.serial_no if is_referenced else None,
				"rebut_cause": "Manipulation",
			}
		)
		movement.insert(ignore_permissions=True)
		row.movement_ref = movement.name
