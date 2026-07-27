# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import unidecode


class Company(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.contacts.contacts import Contacts

		company_name: DF.Data | None
		company_type: DF.Literal["Provider", "Client"]
		contacts: DF.Table[Contacts]
		location: DF.Data | None
		shortname: DF.Data | None
		website: DF.Data | None
	# end: auto-generated types

	def autoname(self):
		self.company_name = unidecode.unidecode(str(self.company_name).upper())
		self.name = self.company_name

	pass
