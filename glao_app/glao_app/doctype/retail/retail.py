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

		article_to_retail: DF.Autocomplete

	# end: auto-generated types
	@frappe.whitelist()
	def _get_article_to_retail(self):
		retail_chars = frappe.get_all("Characteristics", filters=[["retail", "=", 1]], fields=["parent"])
		res = frappe.get_all(
			"Article",
			filters=[["name", "in", [p.parent for p in retail_chars]], ["retail_target", "is", "Set"]],
		)
		articles = []
		for p in res:
			all_stock = frappe.get_all(
				"Stock",
				filters=[["article", "=", p.name], ["quantity", ">", 0]],
				fields=["name", "designation", "quantity"],
			)
			for a in all_stock:
				a_ = {}
				places = frappe.get_all("Places Stock", filters=[["parent", "=", a.name]], fields=["place"])
				frappe.msgprint(f"Article: {a.name}, Places: {places}")
				frappe.msgprint(f"Article: {a.name}, Place: {a['place']}")
				articles.append(a)

		return articles

	pass
