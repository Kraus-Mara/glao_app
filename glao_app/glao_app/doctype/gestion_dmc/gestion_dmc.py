# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class GestionDMC(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		delivery_address: DF.Data | None
		dmc_items: DF.Link | None
		dmc_name: DF.Data | None
		project: DF.Link | None
		status: DF.Literal["Untreated", "Validated", "Partially validated"]
	# end: auto-generated types

	pass
