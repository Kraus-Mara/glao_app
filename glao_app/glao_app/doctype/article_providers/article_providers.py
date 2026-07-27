# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ArticleProviders(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		last_price: DF.Currency
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		part_number: DF.Data | None
		price_date: DF.Date | None
		providers: DF.Link | None
	# end: auto-generated types

	def autoname(self):
		self.name = str(self.providers) + "-" + str(self.part_number)

	pass
