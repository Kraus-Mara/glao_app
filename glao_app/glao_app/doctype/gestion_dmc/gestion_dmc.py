# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from glao_app.glao_app.doctype.gestion_dmc_items.gestion_dmc_items import GestionDMCItems
from glao_app.glao_app.doctype.movement import movement
from frappe.model.naming import getseries, make_autoname


class GestionDMC(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.gestion_dmc_compositions.gestion_dmc_compositions import (
			GestionDMCCompositions,
		)
		from glao_app.glao_app.doctype.gestion_dmc_items.gestion_dmc_items import GestionDMCItems

		client: DF.Data | None
		compositions_de_dmc: DF.Table[GestionDMCCompositions]
		delivery_address: DF.Data | None
		delivery_date: DF.Date | None
		dmc_name: DF.Data | None
		end_date: DF.Date | None
		gestion_items: DF.Table[GestionDMCItems]
		job_no: DF.Data | None
		notes: DF.SmallText | None
		project: DF.Link | None
		starting_date: DF.Date | None
		state: DF.Literal["Draft", "Validated"]
		status: DF.Literal["Draft", "Validated", "Partially validated", "Shipped"]
	# end: auto-generated types

	def autoname(self):
		if not self.dmc_name:
			self.name = make_autoname("DMC-.#")
		else:
			series = getseries(str(self.dmc_name), 1)
			self.name = str(self.dmc_name) + "-" + series

	def recup_compo(self):
		compos = frappe.get_all("Composition")[0].name
		frappe.db.set_value("Composition", compos, "place", "BAT2/MAG2/ETAGEREJ")
		frappe.db.set_value("Composition", compos, "not_available", 0)
		return 1

	def validate(self):
		if self.state == "Draft":
			# self.recup_compo()
			# return 1
			self._save_dmc()

		else:
			self._validation_verif()
			self._save_dmc()

	def _validation_verif(self):
		"""Attribute the status depending of the state of the items"""
		if self.state != "Validated":
			return

		self.status = "Draft"

		items_status = []
		if self.gestion_items:
			for r in self.gestion_items:
				if bool(r.item_from_stock and r.true_quantity > 0):
					items_status.append(2 if r.true_quantity == r.quantity else 1)
				else:
					items_status.append(0)

		compos_valid = (
			[bool(r.composition and r.quantity > 0) for r in self.compositions_de_dmc]
			if self.compositions_de_dmc
			else []
		)

		has_items_val = all(s == 2 for s in items_status) if items_status else True
		has_compos_val = all(compos_valid) if compos_valid else True

		has_items_part = any(s > 0 for s in items_status)
		has_compos_part = any(compos_valid)

		contains_partial_item = any(s == 1 for s in items_status)

		if has_items_val and has_compos_val:
			self.status = "Validated"
		elif (has_items_part or has_compos_part) or contains_partial_item:
			self.status = "Partially validated"
		else:
			frappe.throw("Impossible de valider")

	def _save_dmc(self):
		errors = []

		self._check_places()

		seen_sn_items = set()
		for row in self.gestion_items:
			if row.item_from_stock and "-SN-" in str(row.item_from_stock):
				if row.item_from_stock in seen_sn_items:
					frappe.throw(
						f"L'article avec numéro de série {row.item_from_stock} est présent sur plusieurs lignes. "
						f"Il est impossible de réserver deux fois le même article -SN-."
					)
				seen_sn_items.add(row.item_from_stock)

		# items
		for row in self.gestion_items:
			if row.saved_item and row.saved_item != row.item_from_stock:
				# did you just change the old item ?
				# In this case, manipulate reserved_quantity from its Stock doctype
				stock = frappe.get_doc("Stock", row.saved_item, for_update=True)
				stock.reserved_quantity -= row.moved_quantity
				stock.save()
				if not row.item_from_stock:
					row.source_place = None
					row.closest_event = None
				row.saved_item = None
				row.reserved = 0
			if row.saved_item and (row.moved_quantity != row.true_quantity):
				is_ref = "-SN-" in str(row.saved_item) or "-BN-" in str(row.saved_item)
				if "-SN-" in str(row.saved_item) and row.true_quantity > 1:
					frappe.throw("Il faut ajouter une ligne pour les articles suivis en serial no")
				stock = frappe.get_doc("Stock", row.saved_item, for_update=True)
				stock.reserved_quantity += row.true_quantity - row.moved_quantity
				if stock.reserved_quantity > stock.quantity_in_spie_tm:
					frappe.throw(
						"No enough items available in stock : "
						+ str(row.item_from_stock)
						+ " (Maybe too much reserved)"
						+ "quantity on spie tm site : "
						+ str(stock.quantity_in_spie_tm)
						+ " of which "
						+ str(stock.reserved_quantity)
						+ " are reserved"
					)
				stock.save()
				row.moved_quantity = row.true_quantity
			if row.reserved or row.no_serving:
				continue
			if not (row.item_from_stock and row.source_place):
				continue

			places = frappe.get_all(
				"Places Stock",
				filters=[["parent", "=", row.item_from_stock], ["place", "like", row.source_place]],
			)
			place = frappe.get_doc("Places Stock", places[0].name)

			if place.quantity < row.true_quantity:
				frappe.throw(
					"Not enough "
					+ str(row.item_from_stock)
					+ ", either add a line with a different source, either add some in the source place."
					+ " Currently, "
					+ str(place.quantity)
					+ " is available in the selected place "
					+ str(row.source_place),
					title="Error",
				)
			if row.true_quantity > 0:
				stock = frappe.get_doc("Stock", row.item_from_stock, for_update=True)
				if self.starting_date and stock.closest_event_date:
					if getdate(stock.closest_event_date) < getdate(self.starting_date):
						frappe.throw(
							f"Impossible de réserver l'article {row.item_from_stock}. "
							f"La date du prochain événement ({stock.closest_event_date}) est antérieure à la date de début de la DMC ({self.starting_date})."
						)
				stock.reserved_quantity += row.true_quantity
				if stock.reserved_quantity > stock.quantity_in_spie_tm:
					frappe.throw("No enough items in stock : " + str(row.item_from_stock))
				stock.save()
				row.moved_quantity = row.true_quantity
				row.saved_item = row.item_from_stock
				row.reserved = 1

		# compositions
		for comp_row in self.compositions_de_dmc:
			if comp_row.comp_saved and (str(comp_row.comp_saved) != str(comp_row.composition)):
				frappe.db.set_value("Composition", comp_row.comp_saved, "reserved", 0)
				comp_row.place_saved = None
				comp_row.comp_saved = None
			if not comp_row.composition or (comp_row.quantity <= 0):
				continue
			if comp_row.no_serving:
				continue
			if not comp_row.comp_saved:
				# check if already reserved and validated :
				cd = frappe.get_doc("Composition", comp_row.composition)
				if cd.reserved:
					is_validated = frappe.get_doc("Gestion DMC", cd.by_dmc).status != "Draft"
					if is_validated:
						frappe.throw(
							"This composition comes from a validated DMC, please use the dedicated tab to modify it"
						)
					else:
						cs = frappe.get_all("Gestion DMC Compositions", filters=[["parent", "=", cd.by_dmc]])
						for c in cs:
							d = frappe.get_doc("Gestion DMC Compositions", c.name, for_update=True)
							if d.composition == comp_row.composition:
								d.composition = None
								c.save()
								break
				frappe.db.set_value("Composition", comp_row.composition, "reserved", 1)
				frappe.db.set_value("Composition", comp_row.composition, "by_dmc", self.name)
				comp_row.moved_quantity = comp_row.quantity
				comp_row.comp_saved = comp_row.composition
		# if warnings:
		#   frappe.msgprint(warnings, title="Attention", as_list=True)

		if errors:
			frappe.throw("\n".join(errors), title="Erreurs lors du Pull")

		# self.status = "Draft"
		frappe.msgprint("DMC enregistrée, articles réservés", title="Confirmation")
		# Passed through all without throwing an error
		if self.status != "Draft":
			if self.status == "Partially validated":
				self.create_next_dmc()
			frappe.get_doc(
				{
					"doctype": "Expedition",
					"dmc": self.name,
					"delivery_date": self.delivery_date,
				}
			).insert(ignore_permissions=True)

	def create_next_dmc(self):
		items_to_add = []
		compos_to_add = []
		for row in self.gestion_items:
			if not row.no_serving:
				if row.item_from_stock and (row.quantity - row.true_quantity) > 0:
					items_to_add.append(
						{
							"doctype": "Gestion DMC Items",
							"article": row.article,
							"quantity": (row.quantity - row.true_quantity),
							"item_from_stock": None,
							"source_place": None,
						}
					)
				if not row.item_from_stock:
					items_to_add.append(
						{
							"doctype": "Gestion DMC Items",
							"article": row.article,
							"quantity": row.quantity,
							"item_from_stock": None,
							"source_place": None,
						}
					)
		for comp_row in self.compositions_de_dmc:
			if not comp_row.no_serving:
				if not comp_row.composition:
					compos_to_add.append(
						{
							"doctype": "Gestion DMC Composition",
							"nomenclature": comp_row.nomenclature,
						}
					)
		frappe.get_doc(
			{
				"doctype": "Gestion DMC",
				"dmc_name": self.name,
				"project": self.project,
				"delivery_address": self.delivery_address,
				"delivery_date": self.delivery_date,
				"creation_dmc": self.name,
				"state": "Draft",
				"status": "Draft",
				"gestion_items": items_to_add,
				"compositions_de_dmc": compos_to_add,
				"notes": self.notes,
			}
		).insert(ignore_permissions=True)

	def new_place(self, place_name: str, parent_place: str, is_group=0, external=True):
		frappe.new_doc(
			"Places",
			place_name=place_name,
			parent_places=parent_place,
			is_group=is_group,
			external=external,
			address=1,
			location=self.delivery_address,
		).save(ignore_permissions=True)

	def _create_client_place(self):
		# Parent place
		self.new_place(place_name=str(self.client), parent_place="CLIENTS", is_group=1)
		# Children places
		# self.new_place(place_name="BOOK", parent_place="CLIENTS/" + str(self.client), external=False)
		self.new_place(place_name="SITE", parent_place="CLIENTS/" + str(self.client))
		self.new_place(place_name="WAIT", parent_place="CLIENTS/" + str(self.client), external=False)

	def _check_places(self):
		# First we check if the place client already exists
		places = frappe.get_all(
			"Places",
			filters=[["name", "like", "CLIENTS/" + str(self.client) + "/SITE"]],
			fields=["name"],
		)  # returns either the place if it exists, neither a null list
		if not places:
			self._create_client_place()
			# So now the place exists

	@frappe.whitelist()
	def get_source_places(self, item_from_stock):
		places = frappe.get_all(
			"Places Stock",
			filters=[
				["parent", "=", item_from_stock],
				["quantity", ">", 0],
			],
			fields=["place", "quantity"],
		)
		litiges = frappe.get_all("Places", filters=[["litige", "=", 1]], fields=["name"])
		for p in litiges:
			if p.name in places:
				places.remove(p.name)
		return places

	@frappe.whitelist()
	def get_items_and_substitutes(self, item_asked):
		substitutes = frappe.get_all(
			"Alternatives", filters=[["parent", "=", item_asked]], fields=["alternative_article"]
		)
		items = frappe.get_all("Stock", filters=[["article", "like", str(item_asked)]])
		if substitutes != []:
			for row in substitutes:
				items += frappe.get_all("Stock", filters=[["article", "like", row.alternative_article]])
		# frappe.msgprint("asked : " + str(item_asked) + " items : " + str(items))
		return items

	@frappe.whitelist()
	def get_composition_from_nomenclature(self, nomenclature):
		compositions = frappe.get_all("Composition", filters=[["nomenclature", "like", nomenclature]])
		return compositions
