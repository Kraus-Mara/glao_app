# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PurchaseCommandItems(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		article: DF.Link | None
		asked_quantity: DF.Int
		designation: DF.Data | None
		needs_date: DF.Date | None
		notes: DF.SmallText | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		pr_reference: DF.Link | None
		project: DF.Link | None
		quantity: DF.Int
		supplier: DF.Link | None
	# end: auto-generated types

	pass
