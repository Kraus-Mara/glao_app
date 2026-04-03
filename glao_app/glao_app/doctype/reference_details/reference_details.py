# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ReferenceDetails(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		article: DF.Link | None
		batch_no: DF.Data | None
		cdl: DF.Date | None
		next_rv: DF.Date | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		quantity_for_batch: DF.Int
		serial_no: DF.Data | None
	# end: auto-generated types

	pass
