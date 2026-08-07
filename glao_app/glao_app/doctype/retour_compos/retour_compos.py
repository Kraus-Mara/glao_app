# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RetourCompos(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		article: DF.Link | None
		article_article: DF.Link | None
		compo_row_name: DF.Data | None
		composition: DF.Link | None
		designation: DF.Data | None
		fabricant: DF.Data | None
		is_sub_item: DF.Check
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		place_for_litigation: DF.Link | None
		quantity: DF.Int
		reason: DF.Literal["", "R", "L", "Incomplete"]
		reference_fabricant: DF.Data | None
		sent_quantity: DF.Int
		sold: DF.Check
		treated: DF.Check
		which_are_issued: DF.Int
	# end: auto-generated types

	pass
