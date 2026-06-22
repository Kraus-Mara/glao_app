# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class GestionDMCCompositions(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		comp_saved: DF.Link | None
		composition: DF.Link | None
		nomenclature: DF.Link | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		place_saved: DF.Link | None
		quantity: DF.Int
	# end: auto-generated types

	pass
