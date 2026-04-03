# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class Article(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from glao_app.glao_app.doctype.alternatives.alternatives import Alternatives
        from glao_app.glao_app.doctype.article_providers.article_providers import ArticleProviders
        from glao_app.glao_app.doctype.assembly_items.assembly_items import AssemblyItems
        from glao_app.glao_app.doctype.characteristics.characteristics import Characteristics
        from glao_app.glao_app.doctype.places_stock_rules.places_stock_rules import PlacesStockRules

        article_name: DF.Data
        chars: DF.Table[Characteristics]
        group: DF.Link
        is_active: DF.Check
        is_assembly: DF.Check
        is_referenced: DF.Check
        items: DF.Table[AssemblyItems]
        manufacturer: DF.Data | None
        notes: DF.Text | None
        old_code: DF.Data | None
        providers: DF.Table[ArticleProviders]
        rules: DF.Table[PlacesStockRules]
        shortname: DF.Data | None
        table_fucy: DF.Table[Alternatives]
    # end: auto-generated types

    def autoname(self):
        if self.is_assembly:
            self.name = make_autoname("STM-C-.#####")
        if self.is_referenced:
            self.name = make_autoname("STM-B-.#####")
        if self.is_assembly == 0 and self.is_referenced == 0:
            self.name = make_autoname("STM-A-.#####")

    def on_save(self):
        if self.is_assembly:
            for item in self.items:
                frappe.msgprint(str(item))
                item.add_tag(f"Est une composition de {self.article_name}")

    pass
