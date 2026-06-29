# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from pydantic_core.core_schema import field_after_validator_function


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
		delivery_date: DF.Date | None
		dmc_items: DF.Table[DMCItems]
		dmc_name: DF.Data | None
		project: DF.Link | None
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

	def _gen_compo(self, to_append: list, quantity: int, nomenclature):
		for count in range(quantity):
			to_append.append(
				{
					"doctype": "Gestion DMC Compositions",
					"nomenclature": nomenclature,
				}
			)

	def _create_gestion_dmc(self):
		gestion_items = []
		for row in self.dmc_items:
			frappe.msgprint(str(row.article))
			flag_serial = False
			if frappe.get_doc("Article", str(row.article)).is_referenced:
				# Absolutely not bug-proof
				list_article_from_stock = frappe.get_all(
					"Stock", filters=[["article", "like", str(row.article)]]
				)
				article_example = frappe.get_doc("Stock", str(list_article_from_stock[0].name))
				if article_example.serial_no:
					flag_serial = True
				self._gen_item(
					gestion_items,
					"Gestion DMC Items",
					row.article,
					row.quantity,
					flag_serial,
				)

			else:
				self._gen_item(
					gestion_items,
					"Gestion DMC Items",
					row.article,
					row.quantity,
					False,
				)
		gestion_compo = []
		for r in self.compositions:
			self._gen_compo(gestion_compo, r.quantity, r.nomenclature)
		frappe.get_doc(
			{
				"doctype": "Gestion DMC",
				"project": self.project,
				"delivery_address": self.delivery_address,
				"delivery_date": self.delivery_date,
				"creation_dmc": self.name,
				"state": "Draft",
				"status": "Draft",
				"gestion_items": gestion_items,
				"compositions_de_dmc": gestion_compo,
			}
		).insert(ignore_permissions=True)

		frappe.msgprint("DMC créée avec succès", title="Confirmation")
