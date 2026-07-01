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
		from glao_app.glao_app.doctype.retour_compos.retour_compos import RetourCompos
		from glao_app.glao_app.doctype.retour_items.retour_items import RetourItems

		place_for_compositions: DF.Link | None
		project: DF.Link | None
		saved: DF.Check
		sent_compositions: DF.Table[RetourCompos]
		sent_items: DF.Table[RetourItems]
	# end: auto-generated types

	def validate(self):
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
			filters=[["place", "=", target_site_place], ["quantity", ">", 0]],
			fields=["parent", "quantity"],
		)

		for stock in stock_items:
			designation = frappe.db.get_value("Stock", stock.parent, "designation") or stock.parent

			self.append(
				"sent_items",
				{
					"item": stock.parent,
					"item_name": designation,
					"sent_quantity": stock.quantity,
				},
			)

		# 3. Récupération des Compositions présentes sur ce lieu
		current_compos = frappe.get_all(
			"Composition", filters=[["place", "=", target_site_place]], fields=["name"]
		)

		for compo in current_compos:
			# Chargement du document complet pour accéder à sa table enfant (.items)
			compo_doc = frappe.get_doc("Composition", compo.name)

			for sub_item in compo_doc.items:
				if sub_item.quantity <= 0:
					continue

				self.append(
					"sent_compositions",
					{
						"composition": compo.name,
						"article": sub_item.item,
						"sent_quantity": sub_item.quantity,
					},
				)

	# ------------------------------------------------------------------
	# Traitement des retours (sold -> mouvements de stock)
	# ------------------------------------------------------------------

	def _get_source_place(self):
		client = frappe.db.get_value("Projects", self.project, "company")
		place = "CLIENTS/" + str(client) + "/SITE"
		if not place:
			frappe.throw(f"Aucun lieu chantier défini pour le projet {self.project}")
		return place

	def _create_movement(self, **kwargs):
		kwargs.setdefault("second", 0)
		frappe.get_doc({"doctype": "Movement", **kwargs}).insert(ignore_permissions=True)

	def _process_returned_items(self):
		source_place = None
		for row in self.sent_items:
			if not row.sold or row.treated:
				continue
			if source_place is None:
				source_place = self._get_source_place()
			self._process_one_item_row(row, source_place)

	def _process_one_item_row(self, row, source_place):
		if row.quantity == row.sent_quantity and not row.which_are_issued:
			# Si l'article entier est retourné mais marqué comme cassé (géré globalement via reason par exemple)
			if row.reason == "Broken" and "-SN-" in (row.item or ""):
				self._flag_stock_as_rebut(row.item)

			self._create_movement(
				type="Transfert",
				article_from_stock=row.item,
				source_place=source_place,
				target_place=row.place_to_stock,
				quantity_to_manipulate=row.quantity,
			)

		elif row.which_are_issued and row.reason in ("Broken", "CDL Passed", "End of life"):
			# Cas où une partie spécifique est issue/rebutée
			if row.reason == "Broken" and "-SN-" in (row.item or ""):
				self._flag_stock_as_rebut(row.item)

			self._create_movement(
				type="Pull",
				article_from_stock=row.item,
				source_place=source_place,
				quantity_to_manipulate=row.which_are_issued,
			)
			remaining = row.quantity - row.which_are_issued
			if remaining > 0:
				self._create_movement(
					type="Transfert",
					article_from_stock=row.item,
					source_place=source_place,
					target_place=row.place_to_stock,
					quantity_to_manipulate=remaining,
				)

		elif row.reason == "Damaged":
			place = frappe.get_doc("Places", str(row.place_to_stock))
			if not place.litige:
				frappe.throw(
					f"Le lieu {row.place_to_stock} n'est pas catégorisé 'litige' (article {row.item})"
				)
			self._create_movement(
				type="Transfert",
				article_from_stock=row.item,
				source_place=source_place,
				target_place=row.place_to_stock,
				quantity_to_manipulate=row.quantity,
			)

		else:
			frappe.throw(
				f"État incohérent pour {row.item} : quantity={row.quantity}, "
				f"sent_quantity={row.sent_quantity}, which_are_issued={row.which_are_issued}, "
				f"reason={row.reason}"
			)

		row.treated = 1

	def _process_returned_compositions(self):
		groups = {}
		for row in self.sent_compositions:
			groups.setdefault(row.composition, []).append(row)
		source_place = None
		for composition, rows in groups.items():
			if not all(r.sold for r in rows):
				continue
			if all(r.treated for r in rows):
				continue
			if source_place is None:
				source_place = self._get_source_place()
			for row in rows:
				if row.treated:
					continue
				self._process_one_composition_row(row, source_place)
			all_rows_for_this_compo = [r for r in self.sent_compositions if r.composition == composition]
			if all(r.treated for r in all_rows_for_this_compo):
				compo_doc = frappe.get_doc("Composition", composition, for_update=True)
				compo_doc.place = self.place_for_compositions
				compo_doc.not_available = 0
				compo_doc.client = None
				compo_doc.project = None
				compo_doc.by_dmc = None
				if any(r.which_are_issued for r in all_rows_for_this_compo):
					compo_doc.complete = 0
					frappe.msgprint(
						msg=f"La composition {compo_doc.name} est maintenant incomplète", title="Attention"
					)
				compo_doc.save(ignore_permissions=True)
			else:
				frappe.get_doc("Composition", composition, for_update=True).save()

	def _process_one_composition_row(self, row, source_place):
		if "-SN-" in (row.article or "") and row.quantity > 1:
			frappe.throw(f"{row.article} est un article série (-SN-), quantité > 1 impossible")

		if row.which_are_issued:
			ct = frappe.get_all(
				"Composition Items",
				filters=[["parent", "=", row.composition], ["item", "=", row.article]],
				fields=["name", "quantity"],
			)
			if not ct:
				frappe.throw(f"Composition Items introuvable : {row.article} dans {row.composition}")

			ct_doc = frappe.get_doc("Composition Items", ct[0].name, for_update=True)
			new_qty = ct_doc.quantity - row.which_are_issued
			if new_qty < 0:
				frappe.throw(
					f"which_are_issued ({row.which_are_issued}) > quantité disponible "
					f"({ct_doc.quantity}) pour {row.article} ({row.composition})"
				)

			ct_doc.quantity = new_qty

			if new_qty == 0:
				ct_doc.saved_item = None
				ct_doc.saved_quantity = 0
				ct_doc.saved_place = None
			else:
				ct_doc.saved_quantity = new_qty

			ct_doc.save(ignore_permissions=True)

			if row.reason in ("Broken", "NP"):
				if row.reason == "Broken" and "-SN-" in (row.article or ""):
					self._flag_stock_as_rebut(row.article)

				self._create_movement(
					type="Pull",
					article_from_stock=row.article,
					source_place=source_place,
					quantity_to_manipulate=row.which_are_issued,
				)
			elif row.reason == "Damaged":
				self._create_movement(
					type="Transfert",
					article_from_stock=row.article,
					source_place=source_place,
					target_place=row.place_for_litigation,
					quantity_to_manipulate=row.which_are_issued,
				)
			else:
				frappe.throw(
					f"which_are_issued défini sans reason valide pour {row.article} ({row.composition})"
				)

		row.treated = 1

	def _flag_stock_as_rebut(self, article_name):
		"""Passe le flag rebut à 1 sur le document Stock correspondant à l'article -SN-."""
		if frappe.db.exists("Stock", article_name):
			st = frappe.get_doc("Stock", article_name, for_update=True)
			st.rebut = 1
			st.save(ignore_permissions=True)
		else:
			frappe.msgprint(f"Attention : Le document Stock pour l'article {article_name} n'existe pas.")

	@frappe.whitelist()
	def get_target_places(self, item):
		valid_places_data = frappe.get_all(
			"Places", filters=[["litige", "=", 0], ["external", "=", 0]], fields=["name"]
		)
		valid_places = [p.name for p in valid_places_data]

		if not valid_places:
			return []

		item_base = item.split("-SN-")[0].split("-BN-")[0] if item else ""

		matching_stock = frappe.get_all(
			"Places Stock",
			filters=[
				["parent", "like", f"{item_base}%"],
				["quantity", ">", 0],
				["place", "in", valid_places],
			],
			fields=["place"],
			order_by="quantity desc",
		)

		priority_places = []
		for s in matching_stock:
			if s.place not in priority_places:
				priority_places.append(s.place)

		final_places = list(priority_places)
		for place in valid_places:
			if place not in final_places:
				final_places.append(place)

		return final_places

	pass
