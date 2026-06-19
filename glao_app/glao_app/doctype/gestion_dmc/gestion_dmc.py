# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

from re import IGNORECASE
import frappe
from frappe.model.document import Document

from glao_app.glao_app.doctype.gestion_dmc_items.gestion_dmc_items import GestionDMCItems


class GestionDMC(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.gestion_dmc_compositions.gestion_dmc_compositions import (
			GestionDMCCompositions,
		)
		from glao_app.glao_app.doctype.gestion_dmc_items.gestion_dmc_items import GestionDMCItems

		client: DF.Data | None
		compositions_de_dmc: DF.Table[GestionDMCCompositions]
		delivery_address: DF.Data | None
		dmc_name: DF.Data | None
		end_date: DF.Date | None
		gestion_items: DF.Table[GestionDMCItems]
		project: DF.Link | None
		starting_date: DF.Date | None
		status: DF.Literal["Untreated", "Validated", "Partially validated"]
	# end: auto-generated types

	def validate(self):
		if self.status == "Untreated":
			return 1
		else:
			self.valider_dmc()

	def _validation_verif(self):
		if self.status not in ["Validated", "Partially validated"]:
			return
		# True if validated, else False
		is_val = self.status == "Validated"

		# all() for validated
		# and any() either
		cond_items = (
			(
				all(row.item_from_stock for row in self.gestion_items)
				if is_val
				else any(row.item_from_stock and row.true_quantity != 0 for row in self.gestion_items)
			)
			if self.gestion_items
			else True
		)

		cond_compos = (
			(
				all(row.composition for row in self.compositions_de_dmc)
				if is_val
				else any(row.composition and row.quantity != 0 for row in self.compositions_de_dmc)
			)
			if self.compositions_de_dmc
			else True
		)
		# validated need both tables to be True
		if is_val and cond_items and cond_compos:
			return 1

		err = []
		if not cond_items:
			err.append("Des items posent un problème pour valider")
		if not cond_compos:
			err.append("Des compos posent un problème pour valider")

		# err showed only if (for validated) one flag is false, and showed if both flags (for partially validated) are false
		if (is_val and err) or (not is_val and len(err) == 2):
			frappe.throw(err, as_list=True)

	# def _dates_verif(self):

	def _save_dmc(self):
		warnings = []
		errors = []

		self._check_places()
		# items
		for row in self.gestion_items:
			if row.saved_item != row.item_from_stock:
				# did you just change the old item ?
				# In this case, take the row.movement_ref, and revert it, then reserved = 0
				movement_doc = frappe.get_doc("Movement", str(row.movement_ref))

				is_ref = "-SN-" in str(row.saved_item) or "-BN-" in str(row.saved_item)

				frappe.get_doc(
					{
						"doctype": "Movement",
						"type": "Transfert",
						"second": movement_doc.second,
						"article_from_stock": movement_doc.item_from_stock,
						"article_name": movement_doc.article,
						"source_place": movement_doc.target_place,
						"target_place": movement_doc.source_place,
						"quantity_to_manipulate": movement_doc.quantity_to_manipulate,
					}
				).save(ignore_permissions=True)

			if row.reserved:
				continue
			if not row.item_from_stock:
				continue
			place = frappe.get_doc(
				"Places Stock",
				str(
					frappe.get_all(
						"Places Stock",
						filters=[["parent", "=", row.item_from_stock], ["place", "like", row.source_place]],
					)[0].name
				),
			)
			if place.quantity < row.true_quantity:
				frappe.throw(
					"Not enough "
					+ str(row.item_from_stock)
					+ ", either add a line with a different source, either add some in the source place."
					+ " Currently, "
					+ str(place.quantity)
					+ " is available in the selected place "
					+ str(row.source_place),
					title="Error",
				)
			if row.true_quantity > 0:
				self._transfer_item(
					row, frappe.get_doc("Places", "CLIENTS/" + str(self.client) + "/Book").name
				)
				# Item transfered in the "book" place, so now its reserved
				row.reserved = 1

		# compositions
		for comp_row in self.compositions_de_dmc:
			if not comp_row.composition or comp_row.quantity <= 0:
				continue

			comp_doc = frappe.get_doc("Composition", str(comp_row.composition))
			# if comp_doc.not_available:
			# frappe.throw(str(comp_row.composition) + " n'est pas disponible")
			self._composition_booking(
				comp_row, frappe.get_doc("Places", "CLIENTS/" + str(self.client) + "/Book").name
			)
		# if warnings:
		#   frappe.msgprint(warnings, title="Attention", as_list=True)

		if errors:
			frappe.throw("\n".join(errors), title="Erreurs lors du Pull")

		if self.status == "Partially validated":
			frappe.msgprint("DMC partiellement validée", title="Confirmation")
		else:
			frappe.msgprint("DMC validée", title="Confirmation")
		# Passed through all without throwing an error
		# if self.status == "Partially Validated":
		#   self.create_next_dmc()
		# self._send_dmc()

	def create_next_dmc(self):
		items_to_add = []
		compos_to_add = []
		for row in self.gestion_items:
			if row.item_from_stock and (row.quantity - row.true_quantity) > 0:
				items_to_add.append(
					{
						"doctype": "Gestion DMC Items",
						"article": row.article,
						"quantity": (row.quantity - row.true_quantity),
						"item_from_stock": None,
						"source_place": None,
					}
				)
			if not row.item_from_stock:
				items_to_add.append(
					{
						"doctype": "Gestion DMC Items",
						"article": row.article,
						"quantity": row.quantity,
						"item_from_stock": None,
						"source_place": None,
					}
				)

		frappe.get_doc(
			{
				"doctype": "Gestion DMC",
				"dmc_name": self.dmc_name,
				"project": self.project,
				"delivery_address": self.delivery_address,
				"creation_dmc": self.name,
				"status": "Untreated",
				"gestion_items": items_to_add,
				"compositions_de_dmc": compos_to_add,
			}
		).insert(ignore_permissions=True)
		return

	def _pull_item_referenced(self, row):
		movement = frappe.get_doc(
			{
				"doctype": "Movement",
				"type": "Pull",
				"article_from_stock": row.item_from_stock,
				"rebut_cause": "Manipulation",
			}
		)
		movement.insert(ignore_permissions=True)
		row.movement_ref = movement.name

	def new_place(self, place_name: str, parent_place: str, is_group=0, external=True):
		frappe.new_doc(
			"Places",
			place_name=place_name,
			parent_places=parent_place,
			is_group=is_group,
			external=external,
			address=1,
			location=self.delivery_address,
		).save(ignore_permissions=True)

	def _create_client_place(self):
		# Parent place
		self.new_place(place_name=str(self.client), parent_place="CLIENTS", is_group=1)
		# Children places
		self.new_place(place_name="BOOK", parent_place="CLIENTS/" + str(self.client), external=False)
		self.new_place(place_name="SITE", parent_place="CLIENTS/" + str(self.client))
		self.new_place(place_name="WAIT", parent_place="CLIENTS/" + str(self.client), external=False)

	def _composition_booking(self, row, target_place):
		frappe.db.set_value("Composition", str(row.composition), "not_available", 1)
		frappe.db.set_value("Composition", str(row.composition), "place", target_place)

	def _check_places(self):
		# First we check if the place client already exists
		places = frappe.get_all(
			"Places",
			filters=[["name", "like", "CLIENTS/" + str(self.client) + "/Book"]],
			fields=["name"],
		)  # returns either the place if it exists, neither a null list
		if not places:
			self._create_client_place()
			# So now the place exists

	def _transfer_item(self, row, target_place):
		is_ref = "-SN-" in row.item_from_stock or "-BN-" in row.item_from_stock
		frappe.get_doc(
			{
				"doctype": "Movement",
				"type": "Transfert",
				"second": 1 if is_ref else 0,
				"article_from_stock": row.item_from_stock,
				"article_name": row.article,
				"source_place": row.source_place,
				"target_place": target_place,
				"quantity_to_manipulate": None if "-SN-" in row.item_from_stock else row.true_quantity,
			}
		).save(ignore_permissions=True)

	def _pull_item(self, row):
		movement = frappe.get_doc(
			{
				"doctype": "Movement",
				"type": "Pull",
				"second": 0,
				"article_from_stock": row.item_from_stock,
				"source_place": row.source_place,
				"quantity_to_manipulate": row.true_quantity,
				"rebut_cause": "Manipulation",
			}
		)
		movement.insert(ignore_permissions=True)
		row.movement_ref = movement.name

	@frappe.whitelist()
	def get_source_places(self, item_from_stock):
		places = frappe.get_all(
			"Places Stock",
			filters=[
				["parent", "=", item_from_stock],
				["quantity", ">", 0],
			],
			fields=["place", "quantity"],
		)
		return places

	@frappe.whitelist()
	def get_items_and_substitutes(self, item_asked):
		substitutes = frappe.get_all(
			"Alternatives", filters=[["parent", "=", item_asked]], fields=["alternative_article"]
		)
		items = frappe.get_all("Stock", filters=[["article", "like", str(item_asked)]])
		if substitutes != []:
			for row in substitutes:
				items += frappe.get_all("Stock", filters=[["article", "like", row.alternative_article]])
		# frappe.msgprint("asked : " + str(item_asked) + " items : " + str(items))
		return items

	@frappe.whitelist()
	def get_composition_from_nomenclature(self, nomenclature):
		compositions = frappe.get_all("Composition", filters=[["nomenclature", "like", nomenclature]])
		return compositions
