# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Projects(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		company: DF.Link | None
		end_date: DF.Date | None
		job_no: DF.Data | None
		location: DF.Data | None
		project_name: DF.Data | None
		starting_date: DF.Date | None
	# end: auto-generated types

	pass
