# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

from hashlib import new
import frappe
from frappe.core.doctype.doctype import doctype
from frappe.exceptions import UniqueValidationError
from frappe.model.document import Document
from frappe.types import DF
from frappe.utils import now

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
		designation: DF.Data | None
		designation_add: DF.Data | None
		designation_pull: DF.Data | None
		is_referenced: DF.Check
		movement_date: DF.Datetime | None
		placetostock: DF.Table[PlacesStock]
		quantity_to_manipulate: DF.Int
		reference_details: DF.Table[ReferenceDetails]
		second: DF.Check
		serial: DF.Data | None
		source_place: DF.Autocomplete | None
		target_place: DF.Link | None
		total_quantity: DF.Int
		type: DF.Literal["Add", "Pull", "Transfert"]
	# end: auto-generated types

	def autoname(self):
		hour = now().split(".")[0].replace(":", "").replace("-", "")
		self.name = str(hour) + " " + str(self.article)

	def validate(self):
		if self.type == "Add":
			if self.is_referenced:
				self._creer_instances_referenced()
			else:
				self._creer_instances()
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
		self.designation = self.designation_add if self.designation_add is not None else self.designation_pull

	def on_cancel(self):
		if self.is_referenced:
			self._cancel_referenced_instances()
		else:
			self._cancel_normal()

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

	def _creer_instances_referenced(self):
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
						ps_doc.save()
			else:
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

					# from: discuss.frappe.io/t/attributeerror-dict-object-has-no-attribute-is-new/
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
		frappe.msgprint("Articles suivis ajoutés avec succès")

	def quantities_manipulation(self, doc: Document, operand: str):
		"""doc is the target Places Stock"""
		if operand not in ["sub", "add"]:
			frappe.msgprint("Pas le temps pour tes conneries")
		existing = frappe.get_all("Places Stock", filters={"article": self.article, "place": doc.place})
		if existing:
			ps = frappe.get_doc("Places Stock", existing[0].name)
			if operand == "sub":
				new_place_qty = int(str(ps.quantity)) - int(str(doc.quantity))
			else:
				new_place_qty = int(str(ps.quantity)) + int(str(doc.quantity))
			sr = ps.serial
			ps.delete()  # Deleting the child, to replace
			to_insert = frappe.get_doc("Stock", str(self.article), for_update=True)
			to_insert.update(  # Replacing the child
				{
					"place_table": [
						{
							"doctype": "Places Stock",
							"name": str(self.article) + str(doc.place),
							"place": doc.place,
							"quantity": new_place_qty,
							"article": self.article,
							"serial": sr,
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
			frappe.msgprint("Une erreur est survenue : quantity_calculus_optimized(self)")

	def _creer_instances(self):
		for doc in self.placetostock:
			try:
				# Getting all corresponding Places Stock, obviously there's only one
				existing = frappe.get_all(
					"Places Stock",
					filters={"article": self.article, "place": doc.place},
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
								}
							],
						}
					).insert(ignore_if_duplicate=True)
				self.quantity_calculus()  # Updating the quantities of the self.article Stock
				frappe.msgprint("Articles ajoutés")
			except frappe.exceptions.UniqueValidationError:
				frappe.msgprint("An error occured")

	def _cancel_referenced_instances(self):
		for detail in self.reference_details:
			try:
				for e in frappe.get_all("Ref Events"):
					if str(e).startswith(str(self.article) + str(detail.serial_no)):
						e.delete()
				frappe.get_doc("Reference Details", str(detail.name)).delete()  # The child table is deleted
				frappe.get_doc(
					"Stock", str(self.article) + "-SN-" + str(detail.serial_no)
				).delete()  # Then the table is deleted
			except frappe.exceptions.ValidationError:
				frappe.msgprint("An error occured")
		frappe.msgprint("Referenced article deleted from Stock")

	def _cancel_normal(self):
		for doc in self.placetostock:
			try:
				self.quantities_manipulation(doc, "sub")
				self.quantity_calculus()  # Updating the quantities of the self.article Stock
				doc.delete()
			except frappe.exceptions.UniqueValidationError:
				frappe.msgprint("An error occured")

	@frappe.whitelist()
	def scrap_sources(self):
		existing = frappe.get_all(
			"Places Stock",
			filters=[
				["article", "like", self.article_from_stock],
				["quantity", ">", 0],
			],
		)
		sources = []
		if existing:
			for doc in existing:
				temp = frappe.get_doc("Places Stock", doc.name)
				sources.append(self.recursive_parent_places(temp.place))
		return sources

	def recursive_parent_places(self, place, place_path=None):
		"""Should return Batiment/Zone/Etagere/[current place] instead of [current_place], but only
		for the placeholder, not the actual placename"""
		if place_path is None:
			place_path = []
		doc = frappe.get_doc("Places", place) if isinstance(place, str) else place
		place_path.insert(0, doc.name)

		if doc.parent_places:
			self.recursive_parent_places(doc.parent_places, place_path)
		return "/".join(place_path)

	def _pull_referenced(self):
		existing = frappe.get_all("Places Stock")
		if existing:
			for doc in existing:
				if doc.name.startswith(str(self.article_name) + "-SN-" + str(self.serial)):
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
				frappe.msgprint("Pas assez de quantité")
			else:
				# On doit retirer quantity_to_manipulate
				new_place_qty = doc.quantity - self.quantity_to_manipulate
				doc.delete()  # Deleting the child, to replace
				to_insert = frappe.get_doc("Stock", str(self.article_from_stock), for_update=True)
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
				to_save.update({"quantity": int(new_quantity)}).save()
		frappe.msgprint("Articles retirés avec succès")

	def _transfert_referenced(self):
		existing = frappe.get_all("Places Stock")
		if existing:
			for doc in existing:
				if doc.name.startswith(str(self.article_name) + "-SN-" + str(self.serial)):
					# Obviously there's only one place
					temp = frappe.get_doc("Places Stock", doc.name)
					if temp.quantity == 0:
						frappe.msgprint("The article has no quantity, add some before doing this")
					else:
						temp.delete()  # Delete the old place
						to_save = frappe.get_doc("Stock", str(self.article_from_stock), for_update=True)

						to_save.update(
							{
								"quantity": 1,
								"place_table": [
									{
										"doctype": "Places Stock",
										"place": self.target_place,
										"quantity": 1,
										"article": self.article_name,
										"serial": self.serial,
									}
								],
							}
						).save()  # No need to insert, because I already know that there's only one child
			frappe.msgprint("Referenced article transfered", title="Confirmation")

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
			if self.quantity_to_manipulate > doc.quantity:
				frappe.msgprint("Not enough quantity in this place")
			else:
				self._pull_normal()  # Pull quantity_to_manipulate from source_place
				existing = frappe.get_all(
					"Places Stock",
					filters={"article": self.article, "place": self.target_place},
				)
				if existing:
					self.quantities_manipulation(doc, "add")  # not tested yet
				else:
					to_insert = frappe.get_doc("Stock", str(self.article_from_stock), for_update=True)
					to_insert.update(
						{
							"article": self.article,
							"is_referenced": self.is_referenced,
							"quantity": self.quantity_to_manipulate,
							"place_table": [
								{
									"doctype": "Places Stock",
									"name": str(self.article_from_stock) + str(self.target_place),
									"place": self.target_place,
									"quantity": self.quantity_to_manipulate,
									"article": self.article_from_stock,
								}
							],
						}
					).insert(ignore_if_duplicate=True)
				self.quantity_calculus()  # Updating the quantities of the self.article Stock


pass
