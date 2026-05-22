# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Composition(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.composition_items.composition_items import CompositionItems

		items: DF.Table[CompositionItems]
		nomenclature: DF.Link | None
	# end: auto-generated types

	pass
