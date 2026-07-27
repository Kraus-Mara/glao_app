# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import unidecode


class Units(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		conversion_rate: DF.Data | None
		not_si: DF.Check
		to: DF.Link | None
		unit_name: DF.Data | None
	# end: auto-generated types

	def autoname(self):
		self.name = unidecode.unidecode(self.unit_name).upper()

	pass
