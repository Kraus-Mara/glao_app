# Copyright (c) 2026, kr and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now
from frappe.model.naming import make_autoname
from frappe.utils.xlsxutils import make_xlsx
from frappe.utils.pdf import get_pdf


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
	carrier = getattr(expedition, "carrier", None)

	dmc = frappe.get_doc("Gestion DMC", expedition.dmc)

	items_rows = []
	bom_rows = []

	if dmc.gestion_items:
		items_rows = frappe.get_all(
			"Gestion DMC Items",
			filters=[
				["parent", "=", expedition.dmc],
				["parenttype", "=", "Gestion DMC"],
				["no_serving", "=", 0],
			],
			fields=["item_from_stock", "designation", "true_quantity", "closest_event"],
		)

	if dmc.compositions_de_dmc:
		bom_rows = frappe.get_all(
			"Gestion DMC Compositions",
			filters=[
				["parent", "=", expedition.dmc],
				["parenttype", "=", "Gestion DMC"],
				["no_serving", "=", 0],
				["composition", "is", "Set"],
			],
			fields=["composition", "quantity"],
		)

	html_content = frappe.render_template(
		"""
		<div style="font-family: sans-serif; padding: 20px;">
			<h2>Bon de Livraison : {{ expedition.name }}</h2>
			<p><strong>Transporteur :</strong> {{ carrier or 'N/A' }}</p>
			<p><strong>Gestion DMC :</strong> {{ dmc.name }}</p>
			<hr>

			{% if items_rows %}
			<h3>Articles</h3>
			<table style="width: 100%; border-collapse: collapse;" border="1" cellpadding="5">
				<thead>
					<tr style="background-color: #f2f2f2;">
						<th>Item</th>
						<th>Designation</th>
						<th>Quantity</th>
					</tr>
				</thead>
				<tbody>
					{% for row in items_rows %}
					<tr>
						<td>{{ row.item_from_stock or '' }}</td>
						<td>{{ row.designation or '' }}</td>
						<td>{{ row.true_quantity or 0 }}</td>
					</tr>
					{% endfor %}
				</tbody>
			</table>
			{% endif %}

			{% if bom_rows %}
			<h3 style="margin-top: 20px;">Compositions (BoM)</h3>
			<table style="width: 100%; border-collapse: collapse;" border="1" cellpadding="5">
				<thead>
					<tr style="background-color: #f2f2f2;">
						<th>BoM</th>
						<th>Quantity</th>
					</tr>
				</thead>
				<tbody>
					{% for row in bom_rows %}
					<tr>
						<td>{{ row.composition or '' }}</td>
						<td>{{ row.quantity or 0 }}</td>
					</tr>
					{% endfor %}
				</tbody>
			</table>
			{% endif %}
		</div>
	""",
		{
			"expedition": expedition,
			"dmc": dmc,
			"carrier": carrier,
			"items_rows": items_rows,
			"bom_rows": bom_rows,
		},
	)

	# Génération du flux PDF
	pdf_file = get_pdf(html_content)

	frappe.local.response.filename = "BL.pdf"
	frappe.local.response.filecontent = pdf_file
	frappe.local.response.type = "pdf"
