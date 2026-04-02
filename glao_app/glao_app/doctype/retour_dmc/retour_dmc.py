# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RetourDMC(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.dmc_items.dmc_items import DMCItems

		completed: DF.Check
		delivery_address: DF.Data | None
		dmc_items: DF.Table[DMCItems]
		dmc_name: DF.Data | None
		project: DF.Link | None
		treated: DF.Check
	# end: auto-generated types

	pass
