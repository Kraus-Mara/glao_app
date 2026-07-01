# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RetourItems(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		item: DF.Link | None
		item_name: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		place_to_stock: DF.Link | None
		quantity: DF.Int
		reason: DF.Literal["", "Damaged", "Broken", "CDL Passed", "End of life"]
		sent_quantity: DF.Int
		sold: DF.Check
		treated: DF.Check
		which_are_issued: DF.Int
	# end: auto-generated types

	pass
