# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

from hashlib import new
from warnings import filters
import frappe
from frappe.core.doctype.doctype import doctype
from frappe.exceptions import NotFound, UniqueValidationError
from frappe.model.document import Document
from frappe.types import DF
from frappe.utils import now
from frappe.model.naming import make_autoname
from frappe.utils import add_to_date
from frappe.utils.data import today


class Movement(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from glao_app.glao_app.doctype.places_stock.places_stock import PlacesStock
        from glao_app.glao_app.doctype.reference_details.reference_details import ReferenceDetails

        amended_from: DF.Link | None
        article: DF.Link | None
        article_from_stock: DF.Link | None
        article_name: DF.Data | None
        article_referenced: DF.Link | None
        article_to_register: DF.Link | None
        designation: DF.Data | None
        designation_add: DF.Data | None
        designation_pull: DF.Data | None
        has_batch_no: DF.Data | None
        is_referenced: DF.Check
        movement_date: DF.Datetime | None
        placetostock: DF.Table[PlacesStock]
        quantity_stock_entry: DF.Int
        quantity_to_manipulate: DF.Int
        re_des: DF.Data | None
        rebut_cause: DF.Literal["Sur site", "NP", "Rebut", "Conclusion d'inventaire", "Manipulation"]
        reference_details: DF.Table[ReferenceDetails]
        second: DF.Check
        serial: DF.Data | None
        source_place: DF.Autocomplete | None
        stock_entry_designation: DF.Data | None
        target_place: DF.Link | None
        total_quantity: DF.Int
        type: DF.Literal["Stock Entry", "Register", "Add", "Pull", "Transfert"]
    # end: auto-generated types

    def autoname(self):
        hour = now().split(".")[0].replace(":", "").replace("-", "")
        if self.article:
            self.name = make_autoname(str(hour) + " " + str(self.article) + "-.#")
        elif self.article_from_stock:
            self.name = make_autoname(str(hour) + " " + str(self.article_from_stock) + "-.#")
        elif self.article_referenced:
            self.name = make_autoname(str(hour) + " " + str(self.article_referenced) + "-.#")
        elif self.article_to_register:
            self.name = make_autoname(str(hour) + " " + str(self.article_to_register) + "-.#")
        else:
            frappe.msgprint("Une erreur est survenue : probleme sur les autonames")

    def validate(self):
        if self.type == "Add":
            self._creer_instances()
        if self.type == "Stock Entry":
            self._creer_stock_entry()
        if self.type == "Register":
            self._creer_instances_referenced()
        if self.type == "Pull":
            if self.second:
                self._pull_referenced()
            else:
                self._pull_normal()
        if self.type == "Transfert":
            if self.second:
                self._transfert_referenced()
            else:
                self._transfert_normal()
        # self._sort_events_by_closing_date()
        self._count_stock_in_spie()
        self.designation = (
            self.designation_add or self.stock_entry_designation or self.designation_pull or self.re_des
        )

    # def _sort_events_by_closing_date(self):
    #   parent_name = frappe.get_all(
    #       "Stock",
    #       filters=[["article", "like", self.article], ["serial_no", "like", self.serial_no]],
    #   )[0].name
    #
    #   parent_doc = frappe.get_doc("Stock", parent_name, for_update=True)
    #   events = frappe.get_all(
    #       "Ref Events",
    #       filters=[
    #           ["parent", "=", parent_doc],
    #           ["article", "=", self.article],
    #       ],
    #   )
    #   frappe.msgprint(str(events))
    # events.sort(key=lambda e: e.event_date)
    #
    # new_rows = []
    # for event in events:
    #   if event.event == "VGP" and event.passed:
    #       next_date = frappe.utils.add_months(event.event_date, event.increment)
    #       new_rows.append(
    #           {
    #               "doctype": "Ref Events",
    #               "event": "VGP",
    #               "event_date": next_date,
    #               "batch_no": event.batch_no,
    #               "increment": event.increment,
    #               "passed": 0,
    #           }
    #       )
    #
    # for row in new_rows:
    #   self.append("events", row)
    #
    # self.get("events").sort(key=lambda e: e.event_date)

    def _count_stock_in_spie(self):
        if self.article_referenced:
            places_stock = frappe.get_all(
                "Places Stock",
                filters=[["parent", "like", str(self.article_referenced)], ["external", "=", 0]],
                fields=["quantity", "external"],
            )
            qty = sum(row.quantity if row.external == 0 else 0 for row in places_stock)
            frappe.db.set_value("Stock", str(self.article_referenced), "quantity_in_spie_tm", qty)
        elif self.article_to_register:
            # we suppose we're about to modify the not yet registered item AND the registered items
            # first we count the items thats are not yet registered
            all_stocks_not_registered = frappe.get_all(
                "Stock",
                filters=[["article", "like", str(self.article_to_register)], ["not_yet_registered", "=", 1]],
            )
            if all_stocks_not_registered:
                qty = sum(
                    row.quantity if row.external == 0 else 0
                    for row in frappe.get_doc("Stock", str(all_stocks_not_registered[0].name)).place_table
                )
                # frappe.throw(str(qty))
                frappe.db.set_value(
                    "Stock", str(all_stocks_not_registered[0].name), "quantity_in_spie_tm", qty
                )

            all_stocks_registered = frappe.get_all(
                "Stock",
                filters=[["article", "like", str(self.article_to_register)], ["not_yet_registered", "=", 0]],
            )
            for doc in all_stocks_registered:
                qty = sum(row.quantity for row in frappe.get_doc("Stock", str(doc.name)).place_table)
                frappe.db.set_value("Stock", str(doc.name), "quantity_in_spie_tm", qty)
        elif self.article:
            all_places = frappe.get_all(
                "Places Stock",
                filters=[["parent", "like", str(self.article)], ["external", "=", 0]],
                fields=["quantity"],
            )
            qty = sum(row.quantity for row in all_places)
            frappe.db.set_value("Stock", str(self.article), "quantity_in_spie_tm", qty)
        elif self.article_from_stock:
            all_places = frappe.get_all(
                "Places Stock",
                filters=[["parent", "like", str(self.article_from_stock)], ["external", "=", 0]],
                fields=["quantity"],
            )
            qty = sum(row.quantity for row in all_places)
            # frappe.throw(str(qty))
            frappe.db.set_value("Stock", str(self.article_from_stock), "quantity_in_spie_tm", qty)

    def _creer_stock_entry(self):
        existing = frappe.get_all(
            "Stock", filters=[["article", "=", self.article_referenced], ["not_yet_registered", "=", 1]]
        )
        if not existing:
            frappe.get_doc(
                {
                    "doctype": "Stock",
                    "name": str(self.article_referenced),
                    "article": self.article_referenced,
                    "is_referenced": 1,
                    "quantity": self.quantity_stock_entry,
                    "place_table": [
                        {
                            "doctype": "Places Stock",
                            "place": self.target_place,
                            "quantity": self.quantity_stock_entry,
                            "article": self.article_referenced,
                        }
                    ],
                    "not_yet_registered": 1,
                }
            ).insert(ignore_permissions=True)
            frappe.msgprint("Stock Entry enregistrée")
        else:
            existing = frappe.get_all(
                "Stock", filters=[["article", "=", self.article_referenced], ["not_yet_registered", "=", 1]]
            )
            doc = frappe.get_doc("Stock", existing[0].name, for_update=True)
            ps = frappe.get_all(
                "Places Stock", filters=[["parent", "=", existing[0].name], ["place", "=", self.target_place]]
            )
            if ps:
                # frappe.msgprint("ps trouvé")
                ps_doc = frappe.get_doc("Places Stock", ps[0].name, for_update=True)
                new_quantity = int(ps_doc.quantity) + self.quantity_stock_entry
                # frappe.msgprint(
                #   "debug : ancienne qty" + str(ps_doc.quantity) + " et nouvelle qty : " + str(new_quantity)
                # )
                ps_doc.update(
                    {
                        "quantity": int(new_quantity),
                    }
                ).save(ignore_permissions=True)
            else:
                doc.append(
                    "place_table",
                    {
                        "doctype": "Places Stock",
                        "place": self.target_place,
                        "quantity": self.quantity_stock_entry,
                        "article": self.article_referenced,
                    },
                )
                doc.save()
            all_ps = frappe.get_all(
                "Places Stock", filters=[["parent", "=", existing[0].name]], fields="quantity"
            )
            new_quantity = sum(int(doc.quantity) for doc in all_ps) if existing else 0
            if existing:
                to_save = frappe.get_doc("Stock", str(self.article_referenced), for_update=True)
                to_save.update({"quantity": int(new_quantity)}).save()
            else:
                frappe.msgprint("Une erreur est survenue : ligne 183")
            frappe.msgprint("Stock Entry enregistrée")

    def _creer_instances_referenced(self):
        self.article = self.article_to_register
        tampon = frappe.get_all(
            "Stock",
            filters=[
                ["article", "=", self.article],
                ["is_referenced", "=", 1],
                ["not_yet_registered", "=", 1],
            ],
        )
        if not tampon:
            frappe.throw("Aucun Stock Entry trouvé pour cet article. Faites d'abord un 'Stock Entry'.")
        tampon_doc = frappe.get_doc("Stock", tampon[0].name, for_update=True)
        tampon_place_tables = frappe.get_all(
            "Places Stock",
            filters=[["parent", "like", tampon_doc.name], ["place", "=", self.source_place]],
        )
        place_table_doc = frappe.get_doc("Places Stock", tampon_place_tables[0].name)
        tot_quantity = place_table_doc.quantity
        total_to_register = sum(row.quantity_for_batch or 1 for row in self.reference_details)
        if total_to_register <= 0:
            frappe.throw("You did not put reference details in the form, please add some")
        if tot_quantity < total_to_register:
            frappe.throw(f"No enough quantity : {tot_quantity} available, {total_to_register} needed")
        for row in tampon_doc.place_table:
            if row.name == tampon_place_tables[0].name and row.place == self.source_place:
                row.quantity -= total_to_register
                if row.quantity <= 0:
                    tampon_doc.remove(row)
            break
        # frappe.msgprint(str(tampon_doc.place_table))
        tampon_doc.quantity -= total_to_register
        if tampon_doc.quantity <= 0:
            tampon_doc.delete(force=True)
        else:
            tampon_doc.save()

        for detail in self.reference_details:
            detail.article = self.article
            # Here it should separate the stock construction between two types :
            # The issue is that the quantities has to be grouped in the Places Stock but
            # split by batches, how can we do that ? the obvious solution that comes to my mind is
            # to regroup inside the Places Stock by batches, and so it would appear on multiple
            # lines, for each batch : a quantity and a place.
            # As for serials it's already handled
            if detail.cdl:
                event_date = detail.cdl
                event = "DLU"
                try:
                    # frappe.msgprint(str(detail.batch_no))
                    frappe.new_doc(
                        "Stock",
                        article=self.article,
                        is_referenced=self.is_referenced,
                        quantity=detail.quantity_for_batch,
                        batch_no=detail.batch_no,
                        place_table=[
                            {
                                "doctype": "Places Stock",
                                "place": self.target_place,
                                "quantity": detail.quantity_for_batch,
                                "article": self.article,
                                "batch": detail.batch_no,
                                "code_spie_tm": detail.code_spie_tm,
                            }
                        ],
                        events=[
                            {
                                "doctype": "Ref Events",
                                "event": event,
                                "event_date": event_date,
                                "name": str(self.article) + str(detail.batch_no) + str(today()),
                                "batch_no": str(detail.batch_no),
                            },
                        ],
                    ).insert(ignore_if_duplicate=False, ignore_permissions=True)
                except frappe.exceptions.DuplicateEntryError:
                    # Already exists, so we must override the Places Stock line that matches
                    # the batch number with the new quantity
                    docname = frappe.get_all(
                        "Stock",
                        filters=[["article", "like", self.article], ["batch_no", "like", detail.batch_no]],
                    )[0].name
                    doc = frappe.get_doc("Stock", docname, for_update=True)
                    # So here, i am supposed to fetch from the parent doctype, the child, then
                    # increment quantity of an amount of detail.quantity_for_batch
                    # doc.place_table points towards the child,
                    ps = doc.place_table
                    for row in ps:
                        if self.target_place == row.place:
                            row.quantity += detail.quantity_for_batch
                    doc.save()

            elif detail.next_rv:
                event_date = detail.next_rv
                event = "VGP"
                # Here should be the frappe.get_doc(...) for serials
                try:
                    frappe.new_doc(  # For Serial
                        "Stock",
                        article=self.article,
                        is_referenced=self.is_referenced,
                        quantity=1,
                        place_table=[
                            {
                                "doctype": "Places Stock",
                                "place": self.target_place,
                                "quantity": 1,
                                "article": self.article,
                                "serial": detail.serial_no,
                                "code_spie_tm": detail.code_spie_tm,
                            }
                        ],
                        serial_no=detail.serial_no,
                        events=[
                            {
                                "doctype": "Ref Events",
                                "event": event,
                                "event_date": event_date,
                                "name": str(self.article) + str(detail.serial_no) + str(today()),
                            }
                        ],
                    ).insert(ignore_if_duplicate=True, ignore_permissions=True)
                except frappe.exceptions.UniqueValidationError:
                    frappe.msgprint("un des numéros de série existe dans le Stock")
                finally:  # Quantity == 0
                    docname = frappe.get_all(
                        "Stock",
                        filters=[
                            ["article", "like", self.article],
                            ["serial_no", "like", detail.serial_no],
                        ],
                    )[0].name
                    doc = frappe.get_doc("Stock", docname, for_update=True)
                    doc.quantity = 1
                    doc.set(
                        "place_table",
                        [
                            {
                                "doctype": "Places Stock",
                                "place": self.target_place,
                                "quantity": 1,
                                "article": self.article,
                                "serial": detail.serial_no,
                                "code_spie_tm": detail.code_spie_tm,
                            }
                        ],
                    )
                    if detail.fabrication_date and int(detail.incr_years) > 0:
                        end_of_life_date = add_to_date(
                            detail.fabrication_date,
                            years=int(detail.incr_years),
                        )
                        frappe.log_error(
                            f"EOL DATE: {end_of_life_date}, doc events avant: {doc.events}",
                            "DEBUG END OF LIFE",
                        )
                        doc.append(
                            "events",
                            {
                                "doctype": "Ref Events",
                                "event": "End of life",
                                "event_date": add_to_date(
                                    detail.fabrication_date,
                                    years=int(detail.incr_years),
                                ),
                            },
                        )
                    doc.save()  # No need to insert, because I already know that there's only one child
            else:
                try:
                    frappe.new_doc(
                        "Stock",
                        article=self.article,
                        is_referenced=self.is_referenced,
                        quantity=0,  # Calculated at the end
                        place_table=[
                            {
                                "doctype": "Places Stock",
                                "place": self.target_place,
                                "quantity": detail.quantity_for_batch,
                                "article": self.article,
                                "batch": detail.batch_no,
                                "code_spie_tm": detail.code_spie_tm,
                            }
                        ],
                    ).insert(ignore_if_duplicate=False, ignore_permissions=True)
                    self.quantity_calculus()
                except:
                    # Already exists, so we must override the Places Stock line that matches
                    # the batch number with the new quantity
                    docname = frappe.get_all(
                        "Stock",
                        filters=[
                            ["article", "like", self.article],
                        ],
                    )[0].name

                    doc = frappe.get_doc("Stock", docname, for_update=True)
                    ps = frappe.get_all(
                        "Places Stock",
                        filters=[
                            ["parent", "=", docname],
                            ["article", "=", self.article],
                            ["batch", "=", detail.batch_no],
                        ],
                        fields=["name", "quantity"],
                    )
                    if ps:
                        ps_doc = frappe.get_doc("Places Stock", ps[0].name)
                        ps_doc.quantity += detail.quantity_for_batch
                        ps_doc.insert(ignore_if_duplicate=True, ignore_permissions=True)

        frappe.msgprint("Articles suivis ajoutés avec succès")

    def quantities_manipulation(self, doc: Document, operand: str):
        """doc is supposed to be extracted by doing a for doc in placetostock"""
        if operand not in ["sub", "add"]:
            frappe.msgprint("sub or add")
        existing = frappe.get_all("Places Stock", filters={"article": self.article, "place": doc.place})
        if existing:
            ps = frappe.get_doc("Places Stock", existing[0].name)
            if operand == "sub":
                new_place_qty = int(str(ps.quantity)) - int(str(doc.quantity))
            else:
                new_place_qty = int(str(ps.quantity)) + int(str(doc.quantity))
            sr = ps.serial  # Sick move
            ps.delete()  # Deleting the child, to replace
            to_insert = frappe.get_doc("Stock", str(self.article), for_update=True)
            to_insert.update  # Replacing the child
                {
                    "place_table": [
                        {
                            "doctype": "Places Stock",
                            "name": str(self.article) + str(doc.place),
                            "place": doc.place,
                            "quantity": new_place_qty,
                            "article": self.article,
                            "serial": sr,
                            "batch": doc.batch if doc.batch else None,
                        }
                    ],
                }
            ).insert(ignore_if_duplicate=True, ignore_permissions=True)
            # This is an insersion beside the other children, if we save, the other children would
            # be erased

    def quantity_calculus(self):
        # Now we only get the quantity field, no loop, less compute resources
        existing = frappe.get_all("Places Stock", filters={"article": self.article}, fields=["quantity"])
        new_quantity = sum(doc.quantity for doc in existing) if existing else 0
        if existing:
            to_save = frappe.get_doc("Stock", str(self.article), for_update=True)
            to_save.update({"quantity": int(new_quantity)}).save()
        else:
            frappe.throw("An error occured : 444")

    def _creer_instances(self):
        throw_msg = []
        doc_for_assembly = frappe.get_doc("Article", str(self.article))
        if doc_for_assembly.is_assembly:
            for row in doc_for_assembly.items:
                exists = frappe.get_all("Stock", filters=[["article", "like", str(row.item)]])
                if len(exists) == 0:
                    throw_msg.append(
                        "Item jamais instancié : " + str(row.shortname) + " (" + str(row.item) + ")"
                    )
        if len(throw_msg) > 0:
            frappe.throw(throw_msg, as_list=True)

        for row in self.placetostock:
            if row.quantity < 0:
                frappe.throw("Quantity issue")
        for doc in self.placetostock:
            try:
                # Getting all corresponding Places Stock, obviously there's only one
                existing = frappe.get_all(
                    "Places Stock",
                    filters=[["parent", "like", self.article], ["place", "like", doc.place]],
                )
                if existing:
                    self.quantities_manipulation(doc, "add")
                else:
                    # New
                    frappe.get_doc(
                        {
                            "doctype": "Stock",
                            "article": self.article,
                            "is_referenced": self.is_referenced,
                            "quantity": doc.quantity,
                            "place_table": [
                                {
                                    "doctype": "Places Stock",
                                    "name": str(self.article) + str(doc.place),
                                    "place": doc.place,
                                    "quantity": doc.quantity,
                                    "article": self.article,
                                    "batch": doc.batch,
                                }
                            ],
                        }
                    ).insert(ignore_if_duplicate=True)
                self.quantity_calculus()  # Updating the quantities of the self.article Stock
                frappe.msgprint("Articles ajoutés")
            except frappe.exceptions.UniqueValidationError:
                frappe.msgprint("An error occured")

    @frappe.whitelist()
    def scrap_sources(self):
        if self.article_from_stock:
            existing = frappe.get_doc("Stock", str(self.article_from_stock), for_update=True)
            # frappe.msgprint(str(existing.place_table[0]))
        else:
            existing = frappe.get_doc("Stock", str(self.article_to_register), for_update=True)

        sources = []
        for row in existing.place_table:
            sources.append({"place": row.place, "quantity": row.quantity})
        return sources

    def _pull_referenced(self):
        # we should first check if this is a referenced article with a batch number ( that decides
        # if we need to move more than one item)
        checker = frappe.get_doc("Stock", self.article_from_stock)
        if checker.batch_no:
            existing = frappe.get_all(
                "Places Stock",
                filters=[
                    ["article", "like", self.article_name],
                    ["parent", "like", self.article_from_stock],
                    ["place", "like", self.source_place],
                ],
            )
            doc = frappe.get_doc("Places Stock", str(existing[0].name), for_update=True)
            new_qty = doc.quantity - self.quantity_to_manipulate
            if new_qty < 0:
                frappe.throw("Quantité à manipuler trop grande")
            doc.delete()
            to_insert = frappe.get_doc("Stock", str(self.article_from_stock), for_update=True)
            to_insert.append(
                "place_table",
                {
                    "doctype": "Places Stock",
                    "place": self.source_place,
                    "quantity": new_qty,
                    "article": self.article_name,
                },
            ).insert(ignore_permissions=True)
            to_insert.save()
            tot_qty = 0
            new_doc = frappe.get_doc("Stock", str(self.article_from_stock), for_update=True)
            for row in new_doc.place_table:
                tot_qty += row.quantity
            frappe.db.set_value("Stock", str(self.article_from_stock), "quantity", tot_qty)
            # frappe.throw(str(to_insert.name))
        else:
            existing = frappe.get_all(
                "Places Stock",
                filters=[
                    ["article", "like", self.article_name],
                    ["parent", "like", self.article_from_stock],
                ],
            )
            if existing:
                for doc in existing:
                    # frappe.throw(str(doc.name))
                    # if doc.name.startswith(str(self.article_name) + "-SN-" + str(self.serial)):
                    # Obviously there's only one place
                    temp = frappe.get_doc("Places Stock", doc.name)
                    if temp.quantity == 0:
                        frappe.msgprint("The article has no quantity, add some before doing this")
                    else:
                        temp.delete()
                        to_save = frappe.get_doc("Stock", str(self.article_from_stock), for_update=True)
                        to_save.update({"quantity": 0}).save()
                        frappe.msgprint(
                            "Referenced article pulled out of stock",
                            title="Confirmation",
                        )
        # frappe.throw("ah")

    def _pull_normal(self):
        existing = frappe.get_all(
            "Places Stock",
            filters=[
                ["article", "like", self.article_from_stock],
                ["place", "like", self.source_place],
            ],
        )
        if existing:
            doc = frappe.get_doc("Places Stock", existing[0].name)
            if doc.quantity < self.quantity_to_manipulate:
                # Pas OK
                frappe.throw("No enough quantity available", title="Error")
            else:
                # On doit retirer quantity_to_manipulate
                new_place_qty = doc.quantity - self.quantity_to_manipulate
                if new_place_qty == 0:
                    doc.delete()
                    return 1
                # frappe.msgprint("quantité finale : " + str(new_place_qty))

                doc.delete()  # Deleting the child, to replace

                to_insert = frappe.get_doc("Stock", str(self.article_from_stock), for_update=True)
                if new_place_qty > 0:
                    to_insert.update(  # Replacing the child
                        {
                            "place_table": [
                                {
                                    "doctype": "Places Stock",
                                    "name": str(self.article_from_stock) + str(self.source_place),
                                    "place": self.source_place,
                                    "quantity": new_place_qty,
                                    "article": self.article_from_stock,
                                }
                            ],
                        }
                    ).insert(ignore_if_duplicate=True, ignore_permissions=True)

                allps = frappe.get_all("Places Stock", filters={"article": self.article_from_stock})
                new_quantity = 0
                if allps:
                    for doc in allps:
                        ps = frappe.get_doc("Places Stock", doc.name)
                        new_quantity += ps.quantity

                to_save = frappe.get_doc("Stock", str(self.article_from_stock), for_update=True)
                if new_quantity < 0:
                    if to_save.composition is None:
                        frappe.throw("How did you manage to get a negative new_quantity ?")
                else:
                    to_save.update({"quantity": int(new_quantity)}).save()
            frappe.msgprint("Articles retirés avec succès")
        else:
            frappe.msgprint("Les articles n'ont pas été trouvés", indicator="red")

    def _transfert_referenced(self):
        existing = frappe.get_all("Places Stock", filters=[["parent", "=", self.article_from_stock]])
        if not existing:
            frappe.msgprint("Places Stock introuvable pour " + str(self.article_from_stock))
            return
        for doc in existing:
            temp = frappe.get_doc("Places Stock", doc.name)
            if temp.quantity == 0:
                frappe.msgprint("The article has no quantity, add some before doing this")
            else:
                temp.delete()  # Delete the old place
                to_save = frappe.get_doc("Stock", str(self.article_from_stock), for_update=True)

                to_save.append(
                    "place_table",
                    {
                        "doctype": "Places Stock",
                        "place": self.target_place,
                        "quantity": 1,
                        "article": to_save.article,
                        "serial": to_save.serial_no,
                    },
                )
                to_save.quantity = 1
                to_save.save()  # No need to insert, because I already know that there's only one child
            frappe.msgprint("Article suivi transféré avec succès", title="Confirmation")

    def _transfert_normal(self):
        source = frappe.get_all(
            "Places Stock",
            filters=[
                ["article", "like", self.article_from_stock],
                ["place", "like", self.source_place],
            ],
        )
        if source:
            doc = frappe.get_doc("Places Stock", source[0].name)
            new_qty = doc.quantity - self.quantity_to_manipulate
            if new_qty < 0:
                frappe.throw("Not enough quantity in this place")
            else:
                self._pull_normal()  # Pull quantity_to_manipulate from source_place
                existing = frappe.get_all(
                    "Places Stock",
                    filters=[
                        ["parent", "like", str(self.article_from_stock)],
                        ["place", "like", str(self.target_place)],
                    ],
                )
                if existing:
                    # Delete and replace
                    all = frappe.get_all(
                        "Places Stock",
                        filters=[
                            ["parent", "like", str(self.article_from_stock)],
                            ["place", "like", str(self.target_place)],
                        ],
                    )
                    row_qty = (
                        frappe.get_doc("Places Stock", str(all[0].name)).quantity
                        + self.quantity_to_manipulate
                    )
                    to_modify = frappe.get_doc("Stock", str(self.article_from_stock), for_update=True)
                    frappe.get_doc("Places Stock", str(all[0].name)).delete()
                    to_modify.append(
                        "place_table",
                        {
                            "doctype": "Places Stock",
                            "place": self.target_place,
                            "quantity": row_qty,
                            "article": self.article_name,
                        },
                    )
                    to_modify.save()

                else:
                    to_insert = frappe.get_doc("Stock", str(self.article_from_stock), for_update=True)
                    # frappe.throw(str(to_insert))
                    to_insert.append(
                        "place_table",
                        {
                            "doctype": "Places Stock",
                            "place": self.target_place,
                            "quantity": self.quantity_to_manipulate,
                            "article": self.article_name,
                        },
                    )
                    to_insert.save()

                places_stock = frappe.get_all(
                    "Places Stock", filters=[["parent", "like", self.article_from_stock]], fields=["quantity"]
                )
                tot_row = sum(row.quantity for row in places_stock)
                frappe.db.set_value("Stock", str(self.article_from_stock), "quantity", tot_row)
            frappe.msgprint("articles déplacés")


pass
