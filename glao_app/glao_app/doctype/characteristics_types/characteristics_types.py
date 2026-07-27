# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import unidecode


class Characteristicstypes(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.characteristics_unit_link.characteristics_unit_link import CharacteristicsUnitLink

		characteristics_designation: DF.Data | None
		retail: DF.Check
		standard_periodicity: DF.Check
		units: DF.Table[CharacteristicsUnitLink]
	# end: auto-generated types

	def autoname(self):
		self.name = unidecode.unidecode(str(self.characteristics_designation).upper())

	pass
