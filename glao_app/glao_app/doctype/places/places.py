# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Places(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.places_stock_rules.places_stock_rules import PlacesStockRules

		company: DF.Link | None
		extern: DF.Check
		is_active: DF.Check
		is_group: DF.Check
		lft: DF.Int
		location: DF.Data | None
		old_parent: DF.Link | None
		owner_id: DF.Link | None
		parent_places: DF.Link | None
		place_id: DF.Data
		place_name: DF.Data
		place_rules: DF.Table[PlacesStockRules]
		qualité: DF.Check
		rgt: DF.Int
		type: DF.Literal["Etalonnage", "Litige", "En cours d'inventaire", "Indisponible"]
	# end: auto-generated types

	def autoname(self):
		if self.parent_places:
			parent_doc = frappe.get_doc("Places", self.parent_places)
			self.name = self.recursive_name(parent_doc, "") + self.place_name
		else:
			self.name = self.place_name

	def recursive_name(self, doc, fullpath: str):
		if doc.parent_places:
			parent_doc = frappe.get_doc("Places", doc.parent_places)
			fullpath = self.recursive_name(parent_doc, fullpath)
		fullpath += str(doc.place_name) + "/"
		return fullpath

	pass
