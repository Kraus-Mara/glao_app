# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.data import today


class RetourDMC(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.retour_dmc_items.retour_dmc_items import RetourDMCItems

		completed: DF.Check
		delivery_address: DF.Data | None
		dmc_name: DF.Data | None
		gestion_dmc: DF.Link | None
		project: DF.Data | None
		retour_items: DF.Table[RetourDMCItems]
		treated: DF.Check
	# end: auto-generated types

	def before_insert(self):
		if self.gestion_dmc:
			self._prefill_from_gestion()

	def _prefill_from_gestion(self):
		"""Pré-remplit les lignes depuis GestionDMC avec quantity_returned = 0."""
		gestion = frappe.get_doc("GestionDMC", self.gestion_dmc)
		self.dmc_name = gestion.dmc_name
		self.project = gestion.project
		self.delivery_address = gestion.delivery_address
		self.retour_items = []

		for row in gestion.gestion_items:
			self.append(
				"retour_items",
				{
					"doctype": "RetourDMCItems",
					"article": row.article,
					"quantity_expected": row.quantity,
					"quantity_returned": 0,
					"item_from_stock": row.item_from_stock,
					"source_place": row.source_place,
					"lost": 0,
				},
			)

	@frappe.whitelist()
	def confirmer_retour(self):
		"""
		Bouton custom : traite chaque ligne selon le type d'article.
		STM-A : Movement Add
		STM-B : Movement Stock Entry + Register
		Articles perdus : log sur le project.
		"""
		self.save(ignore_permissions=True)

		errors = []
		for row in self.retour_items:
			if row.lost:
				self._log_lost_item(row)
				continue
			if not row.quantity_returned or row.quantity_returned <= 0:
				continue
			try:
				article_name = str(row.article)
				if article_name.startswith("STM-B-"):
					self._retour_referenced(row)
				else:
					self._retour_normal(row)
			except Exception as e:
				errors.append(f"{row.article} : {str(e)}")

		if errors:
			frappe.throw("\n".join(errors), title="Erreurs lors du retour")

		self.treated = 1
		all_returned = all(
			row.lost or row.quantity_returned >= row.quantity_expected for row in self.retour_items
		)
		self.completed = 1 if all_returned else 0
		self.save(ignore_permissions=True)
		frappe.msgprint("Retour confirmé", title="Confirmation")

	def _retour_normal(self, row):
		"""STM-A : Movement Add avec placetostock vers source_place."""
		movement = frappe.get_doc(
			{
				"doctype": "Movement",
				"type": "Add",
				"article": row.article,
				"is_referenced": 0,
				"rebut_cause": "Manipulation",
				"placetostock": [
					{
						"doctype": "Places Stock",
						"place": row.source_place,
						"quantity": row.quantity_returned,
						"article": row.article,
					}
				],
			}
		)
		movement.insert(ignore_permissions=True)

	def _retour_referenced(self, row):
		"""
		STM-B : Stock Entry puis Register via Movement.
		Les infos serial/batch/cdl/next_rv sont lues depuis le Stock doc lié.
		"""
		if not row.item_from_stock:
			frappe.throw(f"Pas de item_from_stock pour {row.article}")

		stock_doc = frappe.get_doc("Stock", row.item_from_stock)

		# Étape 1 : Stock Entry
		stock_entry = frappe.get_doc(
			{
				"doctype": "Movement",
				"type": "Stock Entry",
				"article_referenced": row.article,
				"target_place": row.source_place,
				"quantity_stock_entry": row.quantity_returned,
				"rebut_cause": "Manipulation",
			}
		)
		stock_entry.insert(ignore_permissions=True)

		# Étape 2 : Register
		ref_detail = {
			"doctype": "ReferenceDetails",
			"article": row.article,
			"batch_no": stock_doc.batch_no,
			"serial_no": stock_doc.serial_no,
			"quantity_for_batch": row.quantity_returned,
		}

		# Récupérer l'event pertinent (VGP ou DLU) depuis le stock
		for event in stock_doc.events:
			if event.event == "VGP" and not event.passed:
				ref_detail["next_rv"] = event.event_date
				break
			elif event.event == "DLU":
				ref_detail["cdl"] = event.event_date
				break

		register_mv = frappe.get_doc(
			{
				"doctype": "Movement",
				"type": "Register",
				"article_to_register": row.article,
				"source_place": row.source_place,
				"target_place": row.source_place,
				"is_referenced": 1,
				"rebut_cause": "Manipulation",
				"reference_details": [ref_detail],
			}
		)
		register_mv.insert(ignore_permissions=True)

	def _log_lost_item(self, row):
		"""Enregistre un log frappe pour traçabilité article perdu."""
		frappe.log_error(
			message=(
				f"Article perdu — DMC: {self.dmc_name} | "
				f"Projet: {self.project} | "
				f"Article: {row.article} | "
				f"Stock ref: {row.item_from_stock or 'N/A'} | "
				f"Date: {today()}"
			),
			title=f"Article perdu — {self.project}",
		)
