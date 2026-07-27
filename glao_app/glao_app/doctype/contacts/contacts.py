# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Contacts(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		add_notes: DF.Check
		address: DF.Data | None
		city: DF.Data | None
		country: DF.Data | None
		email: DF.Data | None
		fonction: DF.Data
		lastname: DF.Data
		notes: DF.LongText | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		phone: DF.Data
		postcode: DF.Data | None
		surname: DF.Data
	# end: auto-generated types

	def autoname(self):
		self.name = f"{self.surname} {self.lastname} - {self.fonction} - {self.phone}"

	pass
