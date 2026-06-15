# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CreationDMC(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.dmc_compositions.dmc_compositions import DMCCompositions
		from glao_app.glao_app.doctype.dmc_items.dmc_items import DMCItems

		amended_from: DF.Link | None
		compositions: DF.Table[DMCCompositions]
		delivery_address: DF.Data | None
		dmc_items: DF.Table[DMCItems]
		dmc_name: DF.Data | None
		project: DF.Data | None
	# end: auto-generated types

	def on_submit(self):
		self._create_gestion_dmc()

	def _gen_item(self, to_append: list, doctype: str, article, quantity: int, serial_no: bool):
		if serial_no:
			for count in range(quantity):
				to_append.append(
					{
						"doctype": doctype,
						"article": article,
						"quantity": 1,
						"item_from_stock": None,
						"source_place": None,
					}
				)
		else:
			to_append.append(
				{
					"doctype": doctype,
					"article": article,
					"quantity": quantity,
					"item_from_stock": None,
					"source_place": None,
				}
			)

	# def _gen_compo(self, to_append: list):

	def _create_gestion_dmc(self):
		gestion_items = []
		for row in self.dmc_items:
			list_article_from_stock = frappe.get_all("Stock", filters=[["article", "like", str(row.article)]])
			article_example = frappe.get_doc("Stock", str(list_article_from_stock[0].name))
			self._gen_item(
				gestion_items, "Gestion DMC Items", row.article, row.quantity, article_example.serial_no
			)
		gestion_compo = []
		for rowc in self.compositions:
			gestion_compo.append(
				{
					"doctype": "Gestion DMC Compositions",
					"composition": rowc.composition,
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
				"gestion_items": gestion_items,
				"compositions_de_dmc": gestion_compo,
			}
		).insert(ignore_permissions=True)

		frappe.msgprint("GestionDMC créée avec succès", title="Confirmation")
