import frappe
from frappe.utils import today, add_days, getdate


def check_ref_events():
	threshold = getdate(add_days(today(), 30))

	referenced_stocks = frappe.get_all("Stock", filters={"is_referenced": 1}, fields=["name", "article"])

	for stock in referenced_stocks:
		events = frappe.get_all(
			"Ref Events",
			filters=[
				["parent", "=", stock.name],
				["passed", "=", 0],
				["event_date", "<=", threshold],
			],
			fields=["name", "event", "event_date"],
		)

		for event in events:
			# Évite les doublons
			if frappe.db.exists(
				"Event",
				{
					"subject": f"[{stock.article}] {event.event}",
				},
			):
				continue

			frappe.get_doc(
				{
					"doctype": "Event",
					"subject": f"[{stock.article}] {event.event}",
					"starts_on": event.event_date,
					"event_type": "Public",
					"description": f"Intervention à prévoir sur {stock.article} (Stock: {stock.name})",
					"event_participants": [
						{
							"doctype": "Event Participants",
							"reference_doctype": "User",
							"reference_docname": user.parent,
						}
						for user in frappe.get_all(
							"Has Role",
							filters={"role": "System Manager", "parenttype": "User"},
							fields=["parent"],
						)
					],
				}
			).insert(ignore_permissions=True)

	frappe.db.commit()
