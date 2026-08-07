# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import unidecode
from frappe.model.naming import make_autoname


class RetouretInventaire(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.retour_compos.retour_compos import RetourCompos
		from glao_app.glao_app.doctype.retour_items.retour_items import RetourItems

		place_for_compositions: DF.Link | None
		project: DF.Link | None
		saved: DF.Check
		sent_compositions: DF.Table[RetourCompos]
		sent_items: DF.Table[RetourItems]
	# end: auto-generated types

	def autoname(self):
		self.name = make_autoname(str(self.project) + " RETOUR-" + ".#")

	def validate(self):
		self.place_for_compositions = str(
			frappe.db.get_single_value("Warehouse settings", "hangar_logistique")
		)
		first_save = not self.saved
		if first_save:
			self._fetch_all_stuff()
		self.saved = 1
		self._process_returned_items()
		self._process_returned_compositions()
		self._check_and_close_project()

	def _check_and_close_project(self):
		client = frappe.db.get_value("Projects", self.project, "company")
		if not client:
			return
		target_site_place = f"CLIENTS/{client}/SITE"

		remaining_items = frappe.db.count(
			"Places Stock", filters=[["place", "=", target_site_place], ["quantity", ">", 0]]
		)
		remaining_compos = frappe.db.count("Composition", filters=[["place", "=", target_site_place]])

		if remaining_items == 0 and remaining_compos == 0:
			if frappe.db.exists("Projects", self.project):
				project_doc = frappe.get_doc("Projects", self.project, for_update=True)
				if not project_doc.completed:
					project_doc.completed = 1
					project_doc.save(ignore_permissions=True)
					frappe.msgprint(
						f"Le chantier étant vide, le projet {self.project} a été marqué comme complété."
					)

	def _fetch_all_stuff(self):
		self.set("sent_items", [])
		self.set("sent_compositions", [])

		client = frappe.db.get_value("Projects", self.project, "company")
		if not client:
			frappe.throw(f"Aucune entreprise (company) définie pour le projet {self.project}")

		target_site_place = f"CLIENTS/{client}/SITE"

		stock_items = frappe.get_all(
			"Places Stock",
			filters=[["place", "=", target_site_place], ["quantity", ">", 0], ["parenttype", "=", "Stock"]],
			fields=["parent", "quantity"],
		)

		for stock in stock_items:
			if str(stock.parent).startswith("STM-C") and frappe.db.exists("Article", stock.parent):
				article_doc = frappe.get_doc("Article", stock.parent)

				for _ in range(int(stock.quantity)):
					designation = frappe.db.get_value("Stock", stock.parent, "designation") or stock.parent
					self.append(
						"sent_items",
						{
							"item": stock.parent,
							"item_name": designation,
							"fabricant": article_doc.manufacturer_name,
							"référence_fabricant": article_doc.manufacturer,
							"sent_quantity": 1,
							"is_sub_item": 0,
						},
					)

					if getattr(article_doc, "items", None):
						for sub_item in article_doc.items:
							sub_designation = (
								frappe.db.get_value("Stock", sub_item.item, "designation") or sub_item.item
							)
							self.append(
								"sent_items",
								{
									"item": sub_item.item,
									"item_name": sub_designation,
									"fabricant": article_doc.manufacturer_name,
									"référence_fabricant": article_doc.manufacturer,
									"sent_quantity": sub_item.item_quantity,
									"is_sub_item": 1,
								},
							)
			else:
				stock_doc = frappe.get_doc("Stock", stock.parent)
				designation = frappe.db.get_value("Stock", stock.parent, "designation") or stock.parent
				self.append(
					"sent_items",
					{
						"item": stock.parent,
						"item_name": designation,
						"fabricant": stock_doc.fabricant_hidden,
						"référence_fabricant": stock_doc.ref_constructeur,
						"sent_quantity": stock.quantity,
						"is_sub_item": 0,
					},
				)

		# 2. Récupération des Compositions présentes
		current_compos = frappe.get_all(
			"Composition", filters=[["place", "=", target_site_place]], fields=["name"]
		)

		for compo in current_compos:
			compo_doc = frappe.get_doc("Composition", compo.name)

			for sub_item in compo_doc.items:
				if sub_item.quantity <= 0:
					continue

				if str(sub_item.item).startswith("STM-C") and frappe.db.exists("Article", sub_item.item):
					assembly_doc = frappe.get_doc("Article", sub_item.item)

					for _ in range(int(sub_item.quantity)):
						designation = (
							frappe.db.get_value("Stock", sub_item.item, "designation") or sub_item.item
						)
						self.append(
							"sent_compositions",
							{
								"composition": compo.name,
								"compo_row_name": sub_item.name,
								"article": sub_item.item,
								"designation": designation,
								"sent_quantity": 1,
								"is_sub_item": 0,
							},
						)

						if getattr(assembly_doc, "items", None):
							for ass_item in assembly_doc.items:
								sub_designation = (
									frappe.db.get_value("Stock", ass_item.item, "designation")
									or ass_item.item
								)
								self.append(
									"sent_compositions",
									{
										"composition": compo.name,
										"compo_row_name": sub_item.name,
										"article": ass_item.item,
										"designation": sub_designation,
										"sent_quantity": ass_item.item_quantity,
										"is_sub_item": 1,
									},
								)
				else:
					self.append(
						"sent_compositions",
						{
							"composition": compo.name,
							"compo_row_name": sub_item.name,
							"article": sub_item.item,
							"designation": frappe.db.get_value("Stock", sub_item.item, "designation")
							or sub_item.item,
							"sent_quantity": sub_item.quantity,
							"is_sub_item": 0,
						},
					)

	def _get_source_place(self):
		client = frappe.db.get_value("Projects", self.project, "company")
		place = f"CLIENTS/{client}/SITE"
		if not place:
			frappe.throw(f"Aucun lieu chantier défini pour le projet {self.project}")
		return place

	def _create_movement(self, **kwargs):
		kwargs.setdefault("second", 0)
		frappe.get_doc({"doctype": "Movement", **kwargs}).insert(ignore_permissions=True)

	def _process_returned_items(self):
		source_place = None

		# check the below items of the stm-c
		for i, row in enumerate(self.sent_items):
			if str(row.item).startswith("STM-C") and row.is_sub_item == 0 and row.sold:
				j = i + 1
				all_subs_valid = True
				while j < len(self.sent_items) and self.sent_items[j].is_sub_item == 1:
					sub_row = self.sent_items[j]
					if row.quantity > 0 and sub_row.quantity != sub_row.sent_quantity:
						all_subs_valid = False
						break
					if row.quantity == 0 and sub_row.quantity != 0:
						all_subs_valid = False
						break
					j += 1

				if not all_subs_valid:
					if not row.reason == "Incomplete":
						frappe.throw(
							f"Impossible de solder l'ensemble {row.item} ({row.item_name}) : "
							f"les quantités de ses sous-articles ne sont pas cohérentes avec la quantité du package principal."
						)
		# treat the stm-c
		for i, row in enumerate(self.sent_items):
			if not row.sold or row.treated:
				continue
			if source_place is None:
				source_place = self._get_source_place()

			if str(row.item).startswith("STM-C") and row.is_sub_item == 0:
				if row.quantity > 0 and row.which_are_issued == 0:
					self._create_movement(
						type="Transfert",
						article_from_stock=row.item,
						source_place=source_place,
						target_place=row.place_to_stock,
						quantity_to_manipulate=row.quantity,
					)
				else:
					self._create_movement(
						type="Pull",
						article_from_stock=row.item,
						source_place=source_place,
						quantity_to_manipulate=row.sent_quantity,
					)

				row.treated = 1

				j = i + 1
				while j < len(self.sent_items) and self.sent_items[j].is_sub_item == 1:
					self.sent_items[j].treated = 1
					j += 1
				continue
			# Standard case (stm-a or b)
			if row.is_sub_item == 0:
				if row.quantity > 0:
					self._process_one_item_row(row, source_place)
				else:
					self._create_movement(
						type="Pull",
						article_from_stock=row.item,
						source_place=source_place,
						quantity_to_manipulate=row.sent_quantity,
					)
					row.treated = 1
			else:
				row.treated = 1

	def _process_one_item_row(self, row, source_place):
		if row.quantity <= row.sent_quantity and not row.which_are_issued:
			self._create_movement(
				type="Transfert",
				article_from_stock=row.item,
				source_place=source_place,
				target_place=row.place_to_stock,
				quantity_to_manipulate=row.quantity,
			)
		elif row.which_are_issued:
			if row.reason == "R" and "-SN-" in (row.item or ""):
				self._flag_stock_as_rebut(row.item)
				self._create_movement(
					type="Pull",
					article_from_stock=row.item,
					source_place=source_place,
					quantity_to_manipulate=1,
				)
			elif row.reason == "R":
				if row.quantity > row.which_are_issued:
					self._create_movement(
						type="Transfert",
						article_from_stock=row.item,
						source_place=source_place,
						target_place=row.place_to_stock,
						quantity_to_manipulate=row.quantity - row.which_are_issued,
					)
					self._create_movement(
						type="Pull",
						article_from_stock=row.item,
						source_place=source_place,
						quantity_to_manipulate=row.which_are_issued,
					)
				elif row.quantity == row.which_are_issued:
					self._create_movement(
						type="Pull",
						article_from_stock=row.item,
						source_place=source_place,
						quantity_to_manipulate=row.which_are_issued,
					)
			elif row.reason == "L":
				if row.quantity > row.which_are_issued:
					frappe.throw(
						frappe._(
							f"Please separate the quantities for litigation and stock transfer for item: {0}"
						).format(row.item)
					)
				elif row.quantity == row.which_are_issued:
					self._create_movement(
						type="Transfert",
						article_from_stock=row.item,
						reason=row.reason,
						source_place=source_place,
						target_place=row.place_to_stock,
						quantity_to_manipulate=row.which_are_issued,
					)
		else:
			frappe.throw(
				frappe._(f"Etes-vous sur de la quantité ? {row.item} {row.item_name}, ligne {row.idx}")
			)
		row.treated = 1

	def _process_returned_compositions(self):
		groups = {}
		for row in self.sent_compositions:
			groups.setdefault(row.composition, []).append(row)

		source_place = None
		for composition, rows in groups.items():
			if not all(r.sold for r in rows) or any(r.treated for r in rows):
				continue

			if source_place is None:
				source_place = self._get_source_place()

			has_incomplete_stmc = False
			has_missing_standard_item = False

			for i, row in enumerate(rows):
				if str(row.article).startswith("STM-C") and row.is_sub_item == 0:
					if not getattr(row, "reason", None) and row.quantity == 0:
						has_incomplete_stmc = True
					if getattr(row, "reason", None) == "Incomplete":
						has_incomplete_stmc = True
					else:
						# Validation des sous-articles associés à ce package
						j = i + 1
						all_subs_valid = True
						while j < len(rows) and rows[j].is_sub_item == 1:
							if row.quantity > 0 and rows[j].quantity != rows[j].sent_quantity:
								all_subs_valid = False
								break
							if row.quantity == 0 and rows[j].quantity != 0:
								all_subs_valid = False
								break
							j += 1

						if not all_subs_valid:
							frappe.throw(
								f"Dans la composition {composition}, l'ensemble {row.article} ne peut être traité car ses sous-articles ne sont pas cohérents. "
								f"Sélectionnez 'Incomplete' en cas de manquant."
							)
				elif row.is_sub_item == 0:
					if row.quantity < row.sent_quantity or getattr(row, "reason", None) == "R":
						has_missing_standard_item = True

			compo_doc = frappe.get_doc("Composition", composition, for_update=True)

			for i, row in enumerate(rows):
				if row.is_sub_item == 1:
					row.treated = 1
					continue

				target_row_name = getattr(row, "compo_row_name", None)

				# ================= CAS ENSEMBLE STM-C =================
				if str(row.article).startswith("STM-C"):
					if row.reason in ["Incomplete", "R"]:
						for item_row in compo_doc.items:
							if (target_row_name and item_row.name == target_row_name) or (
								not target_row_name and item_row.item == row.article
							):
								item_row.quantity = max(0, item_row.quantity - 1)
								compo_doc.save(ignore_permissions=True)
								self._create_movement(
									type="Pull",
									article_from_stock=row.article,
									source_place=item_row.saved_place,
									quantity_to_manipulate=1,
								)
								break

					elif row.reason == "L":
						for item_row in compo_doc.items:
							if (target_row_name and item_row.name == target_row_name) or (
								not target_row_name and item_row.item == row.article
							):
								item_row.quantity = max(0, item_row.quantity - 1)
								compo_doc.save(ignore_permissions=True)
								self._create_movement(
									type="Transfert",
									article_from_stock=row.article,
									source_place=item_row.saved_place,
									target_place=row.place_for_litigation,
									quantity_to_manipulate=row.which_are_issued,
								)
								break

					elif not row.reason:
						for item_row in compo_doc.items:
							if (target_row_name and item_row.name == target_row_name) or (
								not target_row_name and item_row.item == row.article
							):
								item_row.quantity = max(0, item_row.quantity - 1)
								compo_doc.save(ignore_permissions=True)
								self._create_movement(
									type="Pull",
									article_from_stock=row.article,
									source_place=item_row.saved_place,
									quantity_to_manipulate=1,
								)
								break

					row.treated = 1
					# Valider les sous-articles rattachés
					j = i + 1
					while j < len(rows) and rows[j].is_sub_item == 1:
						rows[j].treated = 1
						j += 1

				# ================= CAS ARTICLE STANDARD =================
				else:
					for item_row in compo_doc.items:
						if (target_row_name and item_row.name == target_row_name) or (
							not target_row_name and item_row.item == row.article
						):
							missing = max(0, row.sent_quantity - row.quantity)

							if row.which_are_issued:
								if row.reason == "R":
									new_qty = item_row.quantity - row.which_are_issued - missing
									item_row.quantity = max(0, new_qty)
								elif row.reason == "L":
									if not row.place_for_litigation:
										frappe.throw(
											frappe._(
												"Place for litigation not specified for : " + row.article
											)
										)
									new_qty = item_row.quantity - row.which_are_issued - missing
									item_row.quantity = max(0, new_qty)
									compo_doc.save(ignore_permissions=True)

									# Litigation movement
									self._create_movement(
										type="Transfert",
										article_from_stock=row.article,
										source_place=item_row.saved_place,
										target_place=row.place_for_litigation,
										quantity_to_manipulate=row.which_are_issued,
									)
									# Stock fixing
									self._create_movement(
										type="Pull",
										article_from_stock=row.article,
										source_place=item_row.saved_place,
										quantity_to_manipulate=row.which_are_issued,
									)
								if "-SN-" in (row.article or ""):
									self._flag_stock_as_rebut(row.article)
							else:
								# missing or nothing
								new_qty = row.quantity - missing
								item_row.quantity = max(0, new_qty)
								# Stock fixing
								self._create_movement(
									type="Pull",
									article_from_stock=row.article,
									source_place=item_row.saved_place,
									quantity_to_manipulate=missing,
								)
							break
					row.treated = 1

			compo_doc.place = self.place_for_compositions or frappe.db.get_single_value("Hangar log", "place")
			compo_doc.not_available = 0
			compo_doc.client = None
			compo_doc.project = None
			compo_doc.project_client = None
			if hasattr(compo_doc, "by_dmc"):
				compo_doc.by_dmc = None

			compo_doc.complete = 0 if (has_incomplete_stmc or has_missing_standard_item) else 1
			compo_doc.save(ignore_permissions=True)

	def _process_one_composition_row(self, row, source_place):
		compo_doc = frappe.get_doc("Composition", row.composition, for_update=True)

		target_row_name = getattr(row, "compo_row_name", None)

		for item_row in compo_doc.items:
			if (target_row_name and item_row.name == target_row_name) or (
				not target_row_name and item_row.item == row.article
			):
				if row.quantity == 0:
					new_qty = item_row.quantity - row.sent_quantity
					item_row.quantity = max(0, new_qty)
				elif row.which_are_issued:
					new_qty = item_row.quantity - row.which_are_issued
					item_row.quantity = max(0, new_qty)
				break

		compo_doc.save(ignore_permissions=True)
		row.treated = 1

	def _flag_stock_as_rebut(self, article_name):
		if frappe.db.exists("Stock", article_name):
			st = frappe.get_doc("Stock", article_name, for_update=True)
			st.rebut = 1
			st.save(ignore_permissions=True)

	@frappe.whitelist()
	def get_target_places(self, item, reason=None):
		ist = frappe.get_doc("Stock", item)
		places = []
		if reason == "L":
			litigious_places = frappe.get_all(
				"Places",
				filters=[["external", "=", 0], ["litige", "=", 1]],
			)
			for r in ist.place_table:
				if r.place in [p.name for p in litigious_places]:
					places.append(r.place)
			if not places:
				for p in litigious_places:
					places.append(p.name)
			return places

		for r in ist.place_table:
			if not r.external:
				places.append(r.place)
		if not places:
			pla = frappe.get_all("Places", filters=[["external", "=", 0]], fields=["name"])
			for p in pla:
				places.append(p.name)
		return places
