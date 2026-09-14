# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Retail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		article_to_retail: DF.Link
		quantity: DF.Int
		source_place: DF.Autocomplete | None
	# end: auto-generated types

	def _create_movement(self, **kwargs):
		kwargs.setdefault("second", 0)
		frappe.get_doc({"doctype": "Movement", **kwargs}).insert(ignore_permissions=True)

	def validate(self):
		art = frappe.get_doc("Article", self.article_to_retail)

		char = frappe.get_all(
			"Characteristics", filters=[["parent", "=", art.name], ["retail", "=", 1]], fields=["value"]
		)
		if not char:
			frappe.throw("Pas trouvé")
		self._create_movement(
			type="Pull",
			denom="Inventaire",
			explication="Retail",
			article_from_stock=self.article_to_retail,
			source_place=self.source_place,
			quantity_to_manipulate=self.quantity,
		)
		if art.is_referenced:
			self._create_movement(
				type="Stock Entry",
				article_referenced=art.retail_target,
				quantity=self.quantity * int(char[0].value),
				target_place=self.source_place,
			)

			self._create_movement(
				type="Register",
				article_to_register=art.retail_target,
				source_location=self.source_place,
				target_place=self.source_place,
				reference_details=[
					{
						"doctype": "Reference Details",
						"batch_no": art.batch_no,
						"quantity": self.quantity * int(char[0].value),
					}
				],
			)
		self._create_movement(
			type="Add",
			article=art.retail_target,
			denom="Inventaire",
			explication="Retail",
			placetostock=[
				{
					"doctype": "Places Stock",
					"name": str(art.retail_target) + str(self.source_place),
					"place": self.source_place,
					"quantity": self.quantity * int(char[0].value),
				}
			],
		)

	@frappe.whitelist()
	def scrap_sources(self):
		sto = frappe.get_doc("Stock", self.article_to_retail)
		sources = []
		for row in sto.place_table:
			sources.append({"place": row.place, "quantity": row.quantity})
		return sources

	pass
