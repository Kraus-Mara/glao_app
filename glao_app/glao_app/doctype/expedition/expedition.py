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
		expedition_date: DF.Date | None
		job_no: DF.Data | None
		project: DF.Link | None
		status: DF.Literal["Waiting", "Shipped"]
	# end: auto-generated types

	pass

	def autoname(self):
		self.name = make_autoname(str(self.project) + "-" + str(self.client) + " expedition " + ".#")

	def validate(self):

		previous = self.get_doc_before_save()
		previous_status = previous.status if previous else None

		if self.status == "Shipped" and previous_status != "Shipped":
			if not self.expedition_date:
				self.expedition_date = now()
			self._send_dmc()
		else:
			return 1

	def _send_dmc(self):
		"""transfers item to CLIENTS/SITE and substract this quantity in stock.reserved_quantity"""
		dmc_items = frappe.get_all("Gestion DMC Items", filters=[["parent", "=", self.dmc]])
		dmc = frappe.get_doc("Gestion DMC", str(self.dmc))
		project = frappe.get_doc("Projects", self.project)
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
					target_place="CLIENTS/" + str(dmc.client) + "/" + str(dmc.project),
				).save()

				sd = frappe.get_doc("Stock", str(r.item_from_stock), for_update=True)
				sd.reserved_quantity -= r.true_quantity
				sd.save(ignore_permissions=True)
				if project:
					project.append(
						"project_items_sent",
						{
							"article": r.item_from_stock,
							"designation": r.get("designation"),
							"quantity": r.true_quantity,
							"source_place": r.source_place,
							"date": self.expedition_date,
							"expedition": self.name,
						},
					)
		dmc_compos = frappe.get_all("Gestion DMC Compositions", filters=[["parent", "=", self.dmc]])
		for d in dmc_compos:
			c = frappe.get_doc("Gestion DMC Compositions", d.name)
			if c.comp_saved:
				frappe.db.set_value("Composition", c.composition, "not_available", 1)
				frappe.db.set_value(
					"Composition",
					c.composition,
					"place",
					"CLIENTS/" + str(dmc.client) + "/" + str(dmc.project),
				)
				frappe.db.set_value("Composition", c.composition, "reserved", 0)
				frappe.db.set_value("Composition", c.composition, "by_dmc", None)
				if project:
					doc_comp = frappe.get_doc("Composition", c.composition)
					for r in doc_comp.items:
						project.append(
							"project_compositions_sent",
							{
								"composition": c.composition,
								"article": r.item,
								"designation": r.designation,
								"quantity": r.quantity,
								"source_place": r.saved_place,
								"date": self.expedition_date,
								"expedition": self.name,
							},
						)
		if project:
			project.save(ignore_permissions=True)

		frappe.db.set_value("Gestion DMC", dmc.name, "status", "Shipped")
		frappe.msgprint("Items and Compositions were sent with success")

	pass


@frappe.whitelist()
def _get_item_weight(item_code):
	"""
	Retourne le poids (float) d'un article en KG à partir de ses caractéristiques.
	Retourne 0 si non trouvé.
	"""
	if not item_code:
		return 0.0

	try:
		article = frappe.get_doc("Article", item_code)
	except frappe.DoesNotExistError:
		return 0.0

	total_kg = 0.0
	for row in article.chars or []:
		if (row.characteristics_type or "").upper() == "POIDS":
			try:
				value = float(row.value or 0)
			except TypeError, ValueError:
				value = 0.0
			unit = (row.unit or "").upper()
			if unit == "KG":
				total_kg += value
			elif unit == "G":
				total_kg += value / 1000.0
			elif unit == "T":
				total_kg += value * 1000.0
			# autres unités ignorées
	return total_kg


@frappe.whitelist()
def export_expedition_excel(name):
	expedition = frappe.get_doc("Expedition", name)
	carrier = getattr(expedition, "carrier", None)

	project = frappe.get_doc("Projects", expedition.project)
	dmc = frappe.get_doc("Gestion DMC", expedition.dmc)

	cdmc = frappe.get_all(
		"Creation DMC",
		filters=[
			["project", "=", str(expedition.project)],
			["contact", "Is", "Set"],
		],
	)

	contact = "N/A"
	if cdmc:
		crdmc = frappe.get_doc("Creation DMC", cdmc[0])
		contact = crdmc.contact or "N/A"

	# ------------------------------------------------------------------
	# Récupération des articles
	# ------------------------------------------------------------------
	items_rows = []
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

	# Enrichissement avec le poids
	total_weight_items = 0.0
	for row in items_rows:
		unit_weight = _get_item_weight(row.get("item_from_stock"))
		qty = float(row.get("true_quantity") or 0)
		line_weight = unit_weight * qty
		row["unit_weight"] = round(unit_weight, 3)
		row["line_weight"] = round(line_weight, 3)
		total_weight_items += line_weight

	# ------------------------------------------------------------------
	# Récupération des compositions (BoM)
	# ------------------------------------------------------------------
	bom_rows = []
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

	# Poids des compositions : à adapter selon ta logique métier.
	# Ici on suppose qu'une BoM a un poids total stocké ou calculable ;
	# sinon on laisse à 0 pour ne pas fausser le total.
	total_weight_bom = 0.0
	for row in bom_rows:
		qty = float(row.get("quantity") or 0)
		# TODO : remplacer par le vrai calcul du poids d'une composition
		unit_weight = _get_item_weight(row.get("composition"))
		line_weight = unit_weight * qty
		row["unit_weight"] = round(unit_weight, 3)
		row["line_weight"] = round(line_weight, 3)
		total_weight_bom += line_weight

	total_weight = round(total_weight_items + total_weight_bom, 3)

	# ------------------------------------------------------------------
	# Rendu HTML
	# ------------------------------------------------------------------
	html_content = frappe.render_template(
		"""
		<style>
			.bl-container { font-family: sans-serif; font-size: 11px; color: #222; }
			.bl-header { display: flex; justify-content: space-between; align-items: flex-start;
						border-bottom: 2px solid #003a70; padding-bottom: 8px; margin-bottom: 14px; }
			.bl-header h1 { color: #003a70; font-size: 22px; margin: 0 0 4px 0; }
			.bl-header .bl-num { font-size: 13px; margin: 0; }
			.bl-header-right { text-align: right; }
			.bl-header-right p { margin: 2px 0; }

			.bl-parties { width: 100%; border-collapse: collapse; margin-bottom: 14px; }
			.bl-parties td { vertical-align: top; padding: 8px; }
			.bl-party { width: 50%; border: 1px solid #ccc; }
			.bl-party h3 { margin: 0 0 6px 0; font-size: 12px; color: #003a70;
						text-transform: uppercase; }
			.bl-party p { margin: 2px 0; }

			.bl-transport { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
			.bl-transport td { padding: 6px 8px; border: 1px solid #ccc; background: #f7f9fc; }

			.bl-section { color: #003a70; font-size: 13px; margin: 14px 0 6px 0;
						border-bottom: 1px solid #003a70; padding-bottom: 3px; }

			.bl-table { width: 100%; border-collapse: collapse; margin-bottom: 12px; }
			.bl-table th, .bl-table td { border: 1px solid #bbb; padding: 5px 6px; }
			.bl-table th { background: #003a70; color: #fff; font-weight: bold;
						text-align: left; font-size: 11px; }
			.bl-table tbody tr:nth-child(even) { background: #f5f7fa; }
			.bl-table tfoot td { background: #eef3f8; font-weight: bold; }
			.bl-center { text-align: center; }
			.bl-right { text-align: right; }

			.bl-total { width: 100%; border-collapse: collapse; margin-top: 18px; }
			.bl-total-label { background: #003a70; color: #fff; padding: 10px;
							font-weight: bold; text-align: right; font-size: 13px; }
			.bl-total-value { background: #003a70; color: #fff; padding: 10px;
							font-weight: bold; text-align: right; font-size: 14px;
							width: 30%; }
			/* ---------- SIGNATURES ---------- */
			.bl-signatures {
				margin-top: 24px;
				page-break-inside: avoid;
			}

			.bl-sign-table {
				width: 100%;
				border-collapse: separate;
				border-spacing: 12px 0;
			}

			.bl-sign-box {
				width: 50%;
				border: 1px solid #bbb;
				padding: 10px 12px;
				vertical-align: top;
				background: #fafbfd;
			}

			.bl-sign-title {
				margin: 0 0 8px 0;
				font-weight: bold;
				font-size: 12px;
				color: #003a70;
				text-transform: uppercase;
				border-bottom: 1px solid #003a70;
				padding-bottom: 4px;
			}

			.bl-sign-sub {
				margin: 4px 0;
				font-size: 11px;
			}

			.bl-sign-area {
				margin-top: 10px;
				height: 70px;
				border: 1px dashed #aaa;
				background: #fff;
				position: relative;
			}

			.bl-sign-label {
				position: absolute;
				bottom: 4px;
				left: 6px;
				font-size: 9px;
				color: #888;
				font-style: italic;
			}

			.bl-sign-mention {
			margin-top: 14px;
			font-size: 10px;
			font-style: italic;
			color: #555;
			text-align: center;
			}
			.bl-empty {
				background: #fff;
				height: 24px;
				line-height: 24px;
				padding: 4px 6px;
			}
		</style>
        <div class="bl-container">

            <!-- ================= HEADER ================= -->
            <div class="bl-header">
                <div class="bl-header-left">
                    <h1>BON DE LIVRAISON</h1>
                    <p class="bl-num">N° {{ expedition.name }}</p>
                </div>
                <div class="bl-header-right">
                    <p><strong>Affaire :</strong> {{ expedition.project or 'N/A' }}</p>
                    <p><strong>Date :</strong> {{ expedition.expedition_date or 'N/A' }}</p>
                </div>
            </div>

            <!-- ============ EXPEDITEUR / DESTINATAIRE ============ -->
            <table class="bl-parties">
                <tr>
                    <td class="bl-party">
                        <h3>EXPÉDITEUR</h3>
                        <p><strong>SPIE TURBOMACHINERY</strong></p>
                        <p>Z.I du Pont Long</p>
                        <p>5 avenue des Frères Wright</p>
                        <p>64140 LONS, France</p>
                        <p> Mail : contact.tm@spie.com </p>
                    </td>
                    <td class="bl-party">
                        <h3>DESTINATAIRE</h3>
                        <p><strong>{{ expedition.client or 'N/A' }}</strong></p>
                        <p>{{ project.location or 'N/A' }}</p>
                        <p><strong>Contact :</strong> {{ contact }}</p>
                    </td>
                </tr>
            </table>

            <!-- ============ INFOS TRANSPORT ============ -->
            <table class="bl-transport">
                <tr>
                    <td><strong>Transporteur :</strong> {{ carrier or 'N/A' }}</td>
                    <td><strong>Date d'expédition :</strong> {{ expedition.expedition_date or 'N/A' }}</td>
                    <td><strong>Poids total :</strong> {{ total_weight }} kg</td>
                </tr>
            </table>

            <!-- ============ ARTICLES ============ -->
            {% if items_rows %}
            <h3 class="bl-section">Articles</h3>
			<table class="bl-table">
				<thead>
					<tr>
						<th style="width: 15%;">Item</th>
						<th style="width: 37%;">Désignation</th>
						<th style="width: 12%;">Quantité</th>
						<th style="width: 16%;">Poids unit. (kg)</th>
						<th style="width: 20%;">Dimensions</th>
					</tr>
				</thead>
				<tbody>
					{% for row in items_rows %}
					<tr>
						<td>{{ row.item_from_stock or '' }}</td>
						<td>{{ row.designation or '' }}</td>
						<td class="bl-center">{{ row.true_quantity or 0 }}</td>
						<td class="bl-right">{{ '%.3f'|format(row.unit_weight) }}</td>
						<td class="bl-empty">&nbsp;</td>
					</tr>
					{% endfor %}
				</tbody>
				<tfoot>
					<tr>
						<td colspan="3" class="bl-right"><strong>Poids total articles</strong></td>
						<td class="bl-right"><strong>{{ '%.3f'|format(total_weight_items) }}</strong></td>
						<td class="bl-empty">&nbsp;</td>
					</tr>
				</tfoot>
			</table>
            {% endif %}

            <!-- ============ COMPOSITIONS ============ -->
            {% if bom_rows %}
            <h3 class="bl-section">Compositions (BoM)</h3>
			<table class="bl-table">
				<thead>
					<tr>
						<th style="width: 44%;">Composition</th>
						<th style="width: 14%;">Quantité</th>
						<th style="width: 20%;">Poids unit. (kg)</th>
						<th style="width: 22%;">Dimensions</th>
					</tr>
				</thead>
				<tbody>
					{% for row in bom_rows %}
					<tr>
						<td>{{ row.composition or '' }}</td>
						<td class="bl-center">{{ row.quantity or 0 }}</td>
						<td class="bl-right">{{ '%.3f'|format(row.unit_weight) }}</td>
						<td class="bl-empty">&nbsp;</td>
					</tr>
					{% endfor %}
				</tbody>
				<tfoot>
					<tr>
						<td colspan="2" class="bl-right"><strong>Poids total compositions</strong></td>
						<td class="bl-right"><strong>{{ '%.3f'|format(total_weight_bom) }}</strong></td>
						<td class="bl-empty">&nbsp;</td>
					</tr>
				</tfoot>
			</table>
            {% endif %}

            <!-- ============ TOTAL ============ -->
            <table class="bl-total">
                <tr>
                    <td class="bl-total-label">POIDS TOTAL DE L'EXPÉDITION</td>
                    <td class="bl-total-value">{{ '%.3f'|format(total_weight) }} kg</td>
                </tr>
            </table>
            <!-- ============ SIGNATURES ============ -->
			<div class="bl-signatures">
				<table class="bl-sign-table">
					<tr>
						<td class="bl-sign-box">
							<p class="bl-sign-title">Agent de réception / expédition</p>
							<p class="bl-sign-sub">Nom : ______________________________</p>
							<p class="bl-sign-sub">Date : ______________________________</p>
							<div class="bl-sign-area">
								<span class="bl-sign-label">Signature</span>
							</div>
						</td>
						<td class="bl-sign-box">
							<p class="bl-sign-title">Chauffeur</p>
							<p class="bl-sign-sub">Nom : ______________________________</p>
							<p class="bl-sign-sub">Date : ______________________________</p>
							<div class="bl-sign-area">
								<span class="bl-sign-label">Signature</span>
							</div>
						</td>
					</tr>
				</table>

				<p class="bl-sign-mention">
					Le signataire reconnaît avoir reçu les articles listés ci-dessus en bon état apparent.
					Toute réserve doit être formulée par écrit dans les 48 heures.
				</p>
			</div>

        </div>
        """,
		{
			"expedition": expedition,
			"project": project,
			"contact": contact,
			"dmc": dmc,
			"carrier": carrier,
			"items_rows": items_rows,
			"bom_rows": bom_rows,
			"total_weight_items": round(total_weight_items, 3),
			"total_weight_bom": round(total_weight_bom, 3),
			"total_weight": total_weight,
		},
	)

	pdf_file = get_pdf(
		html_content,
		options={
			"page-size": "A4",
			"margin-top": "12mm",
			"margin-bottom": "12mm",
			"margin-left": "12mm",
			"margin-right": "12mm",
			"encoding": "UTF-8",
		},
	)

	frappe.local.response.filename = f"BL_{expedition.name}.pdf"
	frappe.local.response.filecontent = pdf_file
	frappe.local.response.type = "pdf"
