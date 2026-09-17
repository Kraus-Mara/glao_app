# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import unidecode

# import frappe
from frappe.model.document import Document


class Projects(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.project_compositions_sent.project_compositions_sent import ProjectCompositionsSent
		from glao_app.glao_app.doctype.project_items_sent.project_items_sent import ProjectItemsSent

		company: DF.Link | None
		completed: DF.Check
		compositions: DF.Table[ProjectCompositionsSent]
		end_date: DF.Date | None
		items: DF.Table[ProjectItemsSent]
		job_no: DF.Data | None
		location: DF.Data | None
		project_title: DF.Data | None
		starting_date: DF.Date | None
	# end: auto-generated types

	def autoname(self):
		self.name = unidecode.unidecode(str(self.job_no).upper())

	pass
