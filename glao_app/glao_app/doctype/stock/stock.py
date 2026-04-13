# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from glao_app.glao_app.doctype.ref_events.ref_events import RefEvents


class Stock(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from glao_app.glao_app.doctype.maintenance_book.maintenance_book import Maintenancebook
        from glao_app.glao_app.doctype.places_stock.places_stock import PlacesStock
        from glao_app.glao_app.doctype.ref_events.ref_events import RefEvents

        article: DF.Link | None
        batch_no: DF.Data | None
        carnet_de_maintenance: DF.Table[Maintenancebook]
        designation: DF.Data | None
        events: DF.Table[RefEvents]
        is_referenced: DF.Check
        perime: DF.Check
        place_table: DF.Table[PlacesStock]
        quantity: DF.Int
        ref_constructeur: DF.Data | None
        serial_no: DF.Data | None
    # end: auto-generated types

    def autoname(self):
        if self.is_referenced and self.serial_no:
            self.name = str(self.article) + "-SN-" + str(self.serial_no)
        else:
            self.name = str(self.article)

    pass
