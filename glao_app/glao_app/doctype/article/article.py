# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from operator import contains
import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
import unidecode

from glao_app.glao_app.doctype.assembly_items import assembly_items


class Article(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from glao_app.glao_app.doctype.alternatives.alternatives import Alternatives
		from glao_app.glao_app.doctype.article_place_rules.article_place_rules import ArticlePlaceRules
		from glao_app.glao_app.doctype.article_providers.article_providers import ArticleProviders
		from glao_app.glao_app.doctype.assembly_items.assembly_items import AssemblyItems
		from glao_app.glao_app.doctype.characteristics.characteristics import Characteristics

		article_name: DF.Data
		char_name: DF.Data | None
		char_value: DF.Data | None
		chars: DF.Table[Characteristics]
		group: DF.Link
		is_active: DF.Check
		is_assembly: DF.Check
		is_referenced: DF.Check
		items: DF.Table[AssemblyItems]
		manufacturer: DF.Data
		manufacturer_name: DF.Data | None
		notes: DF.Text | None
		old_code: DF.Data | None
		periodicity: DF.Data | None
		place_rules: DF.Table[ArticlePlaceRules]
		providers: DF.Table[ArticleProviders]
		retail_target: DF.Link | None
		shortname: DF.Data | None
		table_fucy: DF.Table[Alternatives]
		total_expected: DF.Int
		total_maximum: DF.Int
		total_minimum: DF.Int
	# end: auto-generated types

	def autoname(self):
		if self.is_assembly:
			self.name = make_autoname("STM-C-.#####")
		if self.is_referenced:
			self.name = make_autoname("STM-B-.#####")
		if self.is_assembly == 0 and self.is_referenced == 0:
			self.name = make_autoname("STM-A-.#####")

	def on_trash(self):
		if self.is_assembly:
			frappe.msgprint(
				"Article list : ",
				title="Deletion of an assembly",
				indicator="red",
			)
			for item in self.items:
				frappe.msgprint(
					str(item.shortname)
					+ " ("
					+ str(item.item)
					+ ", manufacturer reference: "
					+ str(item.reference_man)
					+ ")",
					title="⚠️ Deletion of an assembly ⚠️",
					indicator="red",
				)

	def validate(self):
		self.article_name = unidecode.unidecode(str(self.article_name).upper())
		self.shortname = unidecode.unidecode(str(self.shortname).upper())
		self.manufacturer_name = unidecode.unidecode(str(self.manufacturer_name).upper())
		self.manufacturer = unidecode.unidecode(str(self.manufacturer).upper())
		if contains(str(self.manufacturer), " "):
			frappe.throw("A blank space is present in the manufacturer")
		self._check_chars()
		self._check_assembly_items()
		# TODO : check if minimum quantity is not greater than expected quantity
		# self._check

	def _check_assembly_items(self):
		if self.is_assembly:
			for r in self.items:
				if r.item == self.name:
					frappe.throw(frappe._("An assembly cannot contain itself"))

	def _check_chars(self):  # Fonction de vérification des charactéristiques
		if self.chars:  # Si la table des charactéristiques possède au moins une valeur
			fr = False  # Savoir si on peut décomposer l'objet (ex : Lot de 12)
			fp = False  # Savoir si l'objet possède une potentielle prolongation de validité
			for r in self.chars:
				if r.periodicity and not fp:
					self.periodicity = r.value
					fp = True
				elif r.periodicity and fp:
					frappe.throw(frappe._("You can't have more than one periodicity"))
				if r.retail and not fr:
					self.char_name = r.characteristics_type
					self.char_value = r.value
					fr = True
				elif r.retail and fr:
					frappe.throw(frappe._("You can't have more than one retail easement"))

	@frappe.whitelist()  # Préfixe permettant l'appel de cette fonction depuis le côté client
	def get_units(self, char_type):
		"""Si l'utilisateur selectionne un characteristics_type,
		la fonction lui propose automatiquement les bonnes unités"""
		units = frappe.get_all(
			"Characteristics Unit Link",
			filters=[["parent", "=", char_type]],
			fields=["unit"],
		)
		return units

	@frappe.whitelist()
	def _fetch_place_rules(self):
		pr = frappe.get_all(
			"Place Rules",
			filters=[["article", "=", self.name], ["parenttype", "=", "Places"]],
			fields=["name", "parent", "minimum_quantity", "expected_quantity", "maximum_quantity"],
		)
		return pr

	pass
