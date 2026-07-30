# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now
from frappe.model.naming import make_autoname
from frappe.utils.xlsxutils import make_xlsx


class Expedition(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		carrier: DF.Data | None
		client: DF.Data | None
		delivery_date: DF.Date | None
		dmc: DF.Link | None
		expedition_date: DF.Datetime | None
		job_no: DF.Data | None
		project: DF.Link | None
		status: DF.Literal["Waiting", "Shipped"]
	# end: auto-generated types

	pass

	def autoname(self):
		self.name = make_autoname(str(self.project) + "-" + str(self.client) + " expedition " + ".#")

	def validate(self):
		if self.status == "Shipped":
			self._send_dmc()
			if not self.expedition_date:
				self.expedition_date = now()
		else:
			return 1

	def _send_dmc(self):
		"""transfers item to CLIENTS/SITE and substract this quantity in stock.reserved_quantity"""
		dmc_items = frappe.get_all("Gestion DMC Items", filters=[["parent", "=", self.dmc]])
		dmc = frappe.get_doc("Gestion DMC", str(self.dmc))
		client = dmc.client
		for doc in dmc_items:
			r = frappe.get_doc("Gestion DMC Items", doc.name)
			if r.no_serving:
				continue
			if r.reserved:
				frappe.new_doc(
					doctype="Movement",
					type="Transfert",
					article_from_stock=r.item_from_stock,
					quantity_to_manipulate=r.true_quantity,
					source_place=r.source_place,
					target_place="CLIENTS/" + str(client) + "/SITE",
				).save()

				sd = frappe.get_doc("Stock", str(r.item_from_stock), for_update=True)
				sd.reserved_quantity -= r.true_quantity
				sd.save(ignore_permissions=True)
		dmc_compos = frappe.get_all("Gestion DMC Compositions", filters=[["parent", "=", self.dmc]])
		for d in dmc_compos:
			c = frappe.get_doc("Gestion DMC Compositions", d.name)
			if c.comp_saved:
				frappe.db.set_value("Composition", c.composition, "not_available", 1)
				frappe.db.set_value("Composition", c.composition, "place", "CLIENTS/" + str(client) + "/SITE")
				frappe.db.set_value("Composition", c.composition, "reserved", 0)
				frappe.db.set_value("Composition", c.composition, "by_dmc", None)

		frappe.db.set_value("Gestion DMC", dmc.name, "status", "Shipped")
		frappe.msgprint("Items and Compositions were sent with success")

	pass


@frappe.whitelist()
def export_expedition_excel(name):
	expedition = frappe.get_doc("Expedition", name)
	dmc = frappe.get_doc("Gestion DMC", expedition.dmc)
	alldata = []
	items_data = []
	bom_data = []
	if dmc.gestion_items:
		fields = ["item_from_stock", "designation", "true_quantity", "closest_event"]
		head = [frappe._("Item"), frappe._("Designation"), frappe._("Quantity"), frappe._("Closest Event")]
		items_data = [head]
		all_item_rows = frappe.get_all(
			"Gestion DMC Items",
			filters=[
				["parent", "=", expedition.dmc],
				["parenttype", "=", "Gestion DMC"],
				["no_serving", "=", 0],
			],
			fields=fields,
		)
		items_data += [[row[f] for f in fields] for row in all_item_rows]
		if items_data == [head]:
			items_data = []
	if dmc.compositions_de_dmc:
		fields = ["composition", "quantity"]
		head = [frappe._("BoM"), frappe._("Quantity")]
		bom_data = [head]
		all_bom_rows = frappe.get_all(
			"Gestion DMC Compositions",
			filters=[
				["parent", "=", expedition.dmc],
				["parenttype", "=", "Gestion DMC"],
				["no_serving", "=", 0],
				["composition", "is", "Set"],
			],
			fields=fields,
		)
		bom_data += [[row[f] for f in fields] for row in all_bom_rows]
		if bom_data == [head]:
			bom_data = []
	alldata = items_data + bom_data
	all = make_xlsx(
		data=alldata,
		sheet_name="BL",
	)
	frappe.local.response.filename = f"{name}_export.xlsx"
	frappe.local.response.filecontent = all.getvalue()
	frappe.local.response.type = "download"
