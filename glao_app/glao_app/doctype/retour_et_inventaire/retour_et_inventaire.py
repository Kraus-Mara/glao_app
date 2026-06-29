# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RetouretInventaire(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from glao_app.glao_app.doctype.retour_items.retour_items import RetourItems

        project: DF.Link | None
        saved: DF.Check
        sent_items: DF.Table[RetourItems]
    # end: auto-generated types
	
    # def validate(self):
    #    self.saved = 1
    #    self._fetch_all_stuff()
	
    
    # def _expedier(self):
    #   if self.status != "Draft":
    #       items = []
    #       compos = []
    #       if self.gestion_items:
    #           for row in self.gestion_items:
    #               if row.reserved:
    #                   items.append({row.item_from_stock, row.true_quantity, row.source_place})
    #       if self.compositions_de_dmc:
    #           for r in self.compositions_de_dmc:
    #               if r.comp_saved:
    #                   compos.append({r.composition, r.place_saved})

    pass
