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
		from glao_app.glao_app.doctype.gestion_dmc_compositions.gestion_dmc_compositions import (
			GestionDMCCompositions,
		)
		from glao_app.glao_app.doctype.gestion_dmc_items.gestion_dmc_items import GestionDMCItems

		client: DF.Data | None
		compositions_de_dmc: DF.Table[GestionDMCCompositions]
		delivery_address: DF.Data | None
		dmc_name: DF.Data | None
		gestion_items: DF.Table[GestionDMCItems]
		project: DF.Link | None
		status: DF.Literal["Untreated", "Validated", "Partially validated"]
		yeah: DF.Autocomplete | None
	# end: auto-generated types

	def validate(self):
		if self.status == "Untreated":
			return 1
		else:
			self.valider_dmc()

	def valider_dmc(self):
		# partie items
		all_linked = all(row.item_from_stock for row in self.gestion_items)
		any_linked = any(row.item_from_stock for row in self.gestion_items)

		if not any_linked:
			frappe.throw("Aucun article lié à un stock — veuillez renseigner les champs 'item_from_stock'.")
		if self.status == "Validated" and not all_linked:
			frappe.throw("Il faut lier tous les articles pour avoir le statut validé")
		elif self.status == "Partially validated" and all_linked:
			frappe.throw("c'est quoi ce merdier")
		errors = []

		self._item_booking()
		for row in self.gestion_items:
			if not row.item_from_stock:
				continue
			# Here i am supposed to split the decision between _pull_item() and _pull_referenced_item()
			# places will allow to check the quantities
			all_place = frappe.get_all(
				"Places Stock",
				filters=[
					["parent", "=", row.item_from_stock],
					["place", "like", row.source_place],
				],
			)
			place = frappe.get_doc("Places Stock", str(all_place[0].name))
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

			self._transfer_item(row, frappe.get_doc("Places", "CLIENTS/" + str(self.client) + "/Book").name)

		if errors:
			frappe.throw("\n".join(errors), title="Erreurs lors du Pull")
		# self.save(ignore_permissions=True)
		# frappe.throw("yeah")
		frappe.msgprint(f"DMC validée — statut : {self.status}", title="Confirmation")

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

	def new_place(self, place_name: str, parent_place: str, is_group=0):
		frappe.new_doc(
			"Places",
			place_name=place_name,
			parent_places=parent_place,
			is_group=is_group,
			external=1,
			address=1,
			location=self.delivery_address,
		).save(ignore_permissions=True)

	def _create_client_place(self):
		# Parent place
		self.new_place(place_name=str(self.client), parent_place="CLIENTS", is_group=1)
		# Children places
		self.new_place(place_name="BOOK", parent_place="CLIENTS/" + str(self.client))
		self.new_place(place_name="SITE", parent_place="CLIENTS/" + str(self.client))
		self.new_place(place_name="WAIT", parent_place="CLIENTS/" + str(self.client))

	def _item_booking(self):
		"""To book an item, we simply have to transfer it to Clients/<Client>/Book"""
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
		# row.movement_ref = movement.name
		# frappe.throw("passed")

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
		# frappe.throw("passed")

	@frappe.whitelist()
	def get_source_places(self, item_from_stock):
		# frappe.throw("nn")
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
