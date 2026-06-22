# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class GestionDMCItems(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		article: DF.Link | None
		closest_event: DF.Date | None
		designation: DF.Data | None
		is_referenced: DF.Check
		item_from_stock: DF.Link | None
		moved_quantity: DF.Int
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		quantity: DF.Int
		reserved: DF.Check
		saved_item: DF.Link | None
		saved_place: DF.Link | None
		source_place: DF.Autocomplete | None
		true_quantity: DF.Int
	# end: auto-generated types

	pass
