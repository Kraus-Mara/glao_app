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

	def _create_gestion_dmc(self):
		gestion_items = []
		for row in self.dmc_items:
			gestion_items.append(
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
				"gestion_items": gestion_items,
			}
		).insert(ignore_permissions=True)

		frappe.msgprint("GestionDMC créée avec succès", title="Confirmation")
