# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class PlacesStock(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		article: DF.Link | None
		batch: DF.Data | None
		code_spie_tm: DF.Data | None
		next_event_date: DF.Date | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		place: DF.Link | None
		quantity: DF.Int
		serial: DF.Data | None
	# end: auto-generated types

	def autoname(self):
		if self.serial:
			self.name = str(self.article) + "-SN-" + str(self.serial)
		else:
			self.name = make_autoname(str(self.article) + str(self.place) + "-.#####")


pass
