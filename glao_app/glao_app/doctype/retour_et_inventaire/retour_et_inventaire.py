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

    def validate(self):
        self.saved = 1
        self._fetch_all_stuff()

    def _fetch_all_stuff(self):
        all_dmc = frappe.get_all(
            "Gestion DMC",
            filters=[["project", "=", self.project], ["status", "in", ["Validated", "Partially validated"]]],
        )
        items = []
        compos = []
        for d in all_dmc:
            e = frappe.get_all("Gestion DMC Items", filters=[["parent", "=", d.name]])
            for i in e:
                r = frappe.get_doc("Gestion DMC Items", i.name)
                items.append([r.item_from_stock, r.designation, r.true_quantity]) if r.reserved else None
            for c in frappe.get_all("Gestion DMC Compositions", filters=[["parent", "=", d]]):
                compos.append(c.composition) if c.quantity > 0 else None
        # frappe.throw(str(items))
        for r in items:
            frappe.get_doc(doctype="Retour Items", item=r.item_from_stock, item_name=r.designation,
                           sent_quantity=r.true_quantity)
            self.sent_items.append("sent_items"
                {
                    "doctype": "Retour Items",
                    "item": r.item_from_stock,
                    "item_name": r.designation,
                    "sent_quantity": r.true_quantity,
                }
            ).insert(ignore_permissions=True)

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
