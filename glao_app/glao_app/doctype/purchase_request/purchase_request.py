# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

from warnings import filters
import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class PurchaseRequest(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.purchase_request_items.purchase_request_items import (
			PurchaseRequestItems,
		)

		amended_from: DF.Link | None
		items: DF.Table[PurchaseRequestItems]
		job_no: DF.Link
		needs_date: DF.Date | None
		place: DF.Link | None
		saved: DF.Check
		type: DF.Literal["", "Manual", "Place", "Return"]
	# end: auto-generated types

	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.achat_items.achat_items import AchatItems

		items: DF.Table[AchatItems]
		job_no: DF.Link | None
		place: DF.Link | None
		saved: DF.Check
		type: DF.Literal["", "Manual", "Place", "Return"]

	def validate(self):
		if self.is_new():
			self.items = []
			self._type_fill()
			self.saved = 1

	def autoname(self):
		if self.job_no:
			self.name = make_autoname(frappe._("PR ") + str(self.job_no) + "-.#")
		elif self.place:
			self.name = make_autoname(frappe._("PR ") + str(self.place) + "-.#")
		else:
			self.name = make_autoname(frappe._("PR ") + "Manual" + "-.#")

	def on_submit(self):
		self._add_to_command()

	def _add_to_command(self):
		if not self.items:
			frappe.throw(frappe._("Add items to submit the request"))

		com = frappe.get_all(
			"Purchase Command", filters=[["exported", "=", 0], ["status", "=", "Draft"]], limit=1
		)

		if not com:
			items_to_command = [
				{
					"project": self.job_no,
					"article": row.article,
					"designation": row.designation,
					"supplier": row.providers,
					"asked_quantity": row.quantity,
					"needs_date": self.needs_date,
					"notes": row.notes,
				}
				for row in self.items
			]

			new_cmd = frappe.get_doc(
				{"doctype": "Purchase Command", "project": self.job_no, "items": items_to_command}
			)
			new_cmd.insert(ignore_permissions=True)
		else:
			doc = frappe.get_doc("Purchase Command", com[0].name, for_update=True)
			for r in self.items:
				doc.append(
					"items",
					{
						"project": self.job_no,
						"article": r.article,
						"designation": r.designation,
						"supplier": r.providers,
						"asked_quantity": r.quantity,
						"needs_date": self.needs_date,
						"notes": r.notes,
					},
				)
			doc.flags.ignore_permissions = True
			doc.save()

	def _type_fill(self):
		if self.type == "Place":
			self._get_place_issues()
		elif self.type == "Return":
			self._get_inventory_issues()

	def _get_place_issues(self):
		pr = frappe.get_all(
			"Place Rules",
			filters=[["parent", "=", self.place], ["parenttype", "=", "Places"]],
			fields=["name", "parent", "article", "minimum_quantity", "expected_quantity", "maximum_quantity"],
		)
		for r in pr:
			ps = frappe.get_all(
				"Places Stock",
				filters=[
					["parenttype", "=", "Stock"],
					["place", "=", self.place],
					["article", "=", r.article],
				],
				fields=["parent", "quantity"],
			)
			if ps:
				co = sum([l.quantity for l in ps])
				s = frappe.get_doc("Stock", ps[0].parent)
				if co < r.minimum_quantity:
					self.append(
						"items",
						{
							"article": s.article,
							"designation": s.designation,
							"reference": s.ref_constructeur,
							"quantity": (r.expected_quantity - co),  # quantity left ON site
						},
					)

	def _get_inventory_issues(self):
		project = frappe.get_doc("Projects", str(self.job_no))
		client = project.company
		site = "CLIENTS/" + str(client) + "/SITE"
		ps = frappe.get_all(
			"Places Stock",
			filters=[["place", "=", site], ["parenttype", "=", "Stock"]],
			fields=["parent", "quantity"],
		)
		if ps:
			stock_names = [p.parent for p in ps]
			stocks = frappe.get_all(
				"Stock",
				filters=[["name", "in", stock_names], ["quantity", ">", 0]],
				fields=["name", "designation", "ref_constructeur", "quantity", "article"],
			)
			# f = frappe.get_all(
			# 	"Article Providers",
			# 	filters=[["parent", "=", stock_names]],
			# 	fields=["providers"],
			# 	as_list=True,
			# )
			# pro = str([r.providers for r in f]).join("\n")
			# frappe.throw(pro)
			for s in stocks:
				self.append(
					"items",
					{
						"article": s.article,
						"designation": s.designation,
						"reference": s.ref_constructeur,
						"quantity": s.quantity,  # quantity left ON site
					},
				)

		movements = frappe.get_all(
			"Movement",
			filters=[["type", "=", "Pull"], ["source_place", "=", str(site)]],
			fields=["article_from_stock", "quantity_to_manipulate"],
		)

		if movements:
			for m in movements:
				link_stock = frappe.get_doc("Movement", m)
				art = frappe.get_doc("Stock", str(link_stock.article_from_stock))
				# f = frappe.get_all(
				# 	"Article Providers", filters=[["parent", "=", art]], fields=["providers"], as_list=True
				# )
				# pro = str([r.providers for r in f]).join("\n")
				# frappe.throw(pro)
				self.append(
					"items",
					{
						"article": art.article,
						"designation": art.designation,
						"reference": art.ref_constructeur,
						"quantity": link_stock.quantity_to_manipulate,
					},
				)

	@frappe.whitelist()
	def get_suppliers(self, article):
		if not article:
			return []
		sons = frappe.get_all(
			"Article Providers",
			filters=[["parent", "=", article]],
			fields=["name", "providers", "part_number", "last_price"],
		)
		return sons

	pass
