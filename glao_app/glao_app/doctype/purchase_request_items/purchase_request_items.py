# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PurchaseRequestItems(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		article: DF.Link | None
		designation: DF.Data | None
		fabricant: DF.Data | None
		notes: DF.SmallText | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		part_no: DF.Data | None
		price: DF.Currency
		providers: DF.Link | None
		quantity: DF.Int
		reference: DF.Data | None
		supplier_link: DF.Link | None
	# end: auto-generated types

	pass
