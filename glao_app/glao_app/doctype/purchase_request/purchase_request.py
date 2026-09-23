# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

from warnings import filters
import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils.nestedset import get_descendants_of
from collections import defaultdict


class PurchaseRequest(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.purchase_request_items.purchase_request_items import PurchaseRequestItems

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
		self.items = []

		if not self.place:
			return

		places = [self.place] + list(get_descendants_of("Places", self.place, ignore_permissions=True))

		# Req 1 — Règles
		rules = frappe.get_all(
			"Place Rules",
			filters=[
				["parent", "in", places],
				["parenttype", "=", "Places"],
			],
			fields=["parent", "article", "minimum_quantity", "expected_quantity"],
		)
		if not rules:
			return

		articles = list({r.article for r in rules if r.article})

		# Req 2 — Stocks (tous emplacements + tous articles concernés)
		places_stock = frappe.get_all(
			"Places Stock",
			filters=[
				["parenttype", "=", "Stock"],
				["place", "in", places],
				["article", "in", articles],
			],
			fields=["parent", "place", "article", "quantity"],
		)

		stock_qty = defaultdict(float)
		stock_parent = {}
		for row in places_stock:
			key = (row.place, row.article)
			stock_qty[key] += row.quantity or 0
			stock_parent.setdefault(key, row.parent)

		# Identifier les règles en déficit
		pending = []  # (rule, current_qty, stock_name)
		needed_names = set()
		for r in rules:
			if not r.article:
				continue
			key = (r.parent, r.article)
			co = stock_qty.get(key, 0.0)
			if co < (r.minimum_quantity or 0):
				sname = stock_parent.get(key)
				if sname:
					pending.append((r, co, sname))
					needed_names.add(sname)

		if not pending:
			return

		# Req 3 — Docs Stock nécessaires (pour designation / ref_constructeur)
		stocks = frappe.get_all(
			"Stock",
			filters=[["name", "in", list(needed_names)]],
			fields=["name", "article", "designation", "ref_constructeur"],
		)
		stock_map = {s.name: s for s in stocks}

		for r, co, sname in pending:
			s = stock_map.get(sname)
			if not s:
				continue
			self.append(
				"items",
				{
					"article": s.article,
					"designation": s.designation,
					"reference": s.ref_constructeur,
					"quantity": (r.expected_quantity or 0) - co,
				},
			)

	def _get_inventory_issues(self):
		project = frappe.get_doc("Projects", str(self.job_no))
		client = project.company
		site = "CLIENTS/" + str(client) + "/" + project.name
		# frappe.throw(site)
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
