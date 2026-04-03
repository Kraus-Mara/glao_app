# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RefEvents(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		article: DF.Link | None
		batch_no: DF.Data | None
		event: DF.Literal["VGP", "DLU", "Other"]
		event_date: DF.Date | None
		increment: DF.Int
		intervention_date: DF.Date | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		passed: DF.Check
	# end: auto-generated types

	pass
