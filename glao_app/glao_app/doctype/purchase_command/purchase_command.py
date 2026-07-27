# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class PurchaseCommand(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.purchase_command_items.purchase_command_items import (
			PurchaseCommandItems,
		)

		exported: DF.Check
		items: DF.Table[PurchaseCommandItems]
		status: DF.Data | None
	# end: auto-generated types

	def autoname(self):
		self.name = make_autoname(frappe._("PO") + "-.####")

	def validate(self):
		if not self.status == "Exported":
			if self.exported:
				self.status = "Exported"

	pass
