# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import unidecode


class ArticlesGroup(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		full_group_name: DF.Data | None
		group_name: DF.Data | None
		is_group: DF.Check
		lft: DF.Int
		old_parent: DF.Link | None
		parent_articles_group: DF.Link | None
		periodicity_in_days: DF.Int
		rgt: DF.Int
	# end: auto-generated types

	def autoname(self):
		self.name = unidecode.unidecode(str(self.group_name).upper())

	pass
