# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CompositionItems(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		article_article: DF.Link | None
		closest_event_date: DF.Date | None
		designation: DF.Data | None
		fabricant: DF.Data | None
		item: DF.Link | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		quantity: DF.Int
		référence_fabricant: DF.Data | None
		saved_item: DF.Autocomplete | None
		saved_place: DF.Autocomplete | None
		saved_quantity: DF.Int
	# end: auto-generated types

	pass
