import frappe
from frappe.utils import getdate, date_diff, today, formatdate


def check_and_notify_stock_events():
	"""
	Script journalier :
	1. Marque les événements échus (Fin de vie, VGP, DLU) comme 'passed'.
	2. Notifie le rôle 'Groupe 6' à J-30 et J-15 pour les événements VGP et DLU.
	"""
	today_date = getdate(today())

	suivis = frappe.get_all(
		"Stock", filters=[["is_referenced", "=", 1], ["quantity", ">", 0], ["rebut", "=", 0]]
	)

	recipients = get_groupe_6_recipients()
	if not recipients:
		frappe.logger().warning(
			"check_and_notify_stock_events : aucun utilisateur actif avec le rôle 'Groupe 6'"
		)

	errors = []
	processed = 0
	skipped = 0
	notified_count = 0

	for r in suivis:
		try:
			s = frappe.get_doc("Stock", r.name)
			if not s.events:
				continue

			modified = False

			for e in s.events:
				if not e.event_date:
					continue

				event_date = getdate(e.event_date)
				days_until = date_diff(event_date, today_date)  # négatif si passé

				# ---------- 1. Événements échus ----------
				if e.event == "Fin de vie" and event_date <= today_date:
					if not e.passed:
						e.passed = 1
						modified = True

				if e.event in ("VGP", "DLU") and event_date <= today_date:
					if not e.passed:
						e.passed = 1
						modified = True

				# ---------- 2. Notifications J-30 et J-15 ----------
				if e.event in ("VGP", "DLU") and not e.passed:
					# Palier J-30
					if 15 < days_until <= 30 and not getattr(e, "notified_30", 0):
						send_notification(
							stock_doc=s,
							event=e,
							days_until=days_until,
							threshold=30,
							recipients=recipients,
						)
						e.notified_30 = 1
						modified = True
						notified_count += 1

					# Palier J-15
					elif 0 < days_until <= 15 and not getattr(e, "notified_15", 0):
						send_notification(
							stock_doc=s,
							event=e,
							days_until=days_until,
							threshold=15,
							recipients=recipients,
						)
						e.notified_15 = 1
						modified = True
						notified_count += 1

			if modified:
				s.save(ignore_permissions=True, ignore_version=True)
				# ✅ COMMIT immédiat pour persister les notifs déjà envoyées
				#    et éviter qu'un rollback ultérieur les efface
				frappe.db.commit()
				processed += 1

		except Exception as exc:
			skipped += 1
			errors.append(f"{r.name} : {exc}")
			frappe.logger().warning(f"[check_stock_events] {r.name} ignoré : {exc}")
			# ✅ Rollback uniquement les modifs en cours de ce doc
			frappe.db.rollback()

	frappe.logger().info(
		f"[check_stock_events] Traités : {processed}, ignorés : {skipped}, total : {len(suivis)}"
	)

	return {
		"processed": processed,
		"skipped": skipped,
		"notified": notified_count,
		"total": len(suivis),
		"errors": errors,
	}


# ============================================================
# Helpers
# ============================================================
def get_groupe_6_recipients():
	"""Retourne la liste des utilisateurs actifs avec le rôle Groupe 6."""
	users = frappe.get_all(
		"Has Role",
		filters={"role": "Groupe 6", "parenttype": "User"},
		pluck="parent",
		distinct=True,
	)

	if not users:
		return []

	active_users = frappe.get_all(
		"User",
		filters={
			"name": ["in", users],
			"enabled": 1,
			"user_type": "System User",
		},
		pluck="name",
	)
	return active_users


def send_notification(stock_doc, event, days_until, threshold, recipients):
	"""Crée une Notification Log par destinataire et publie en temps réel."""
	if not recipients:
		return

	subject = f"[Alerte Stock] {event.event} dans {days_until} jour(s) — {stock_doc.name}"
	message = (
		f"<p>L'événement <b>{event.event}</b> approche pour l'article suivant :</p>"
		f"<ul>"
		f"  <li><b>Stock :</b> {stock_doc.name}</li>"
		f"  <li><b>Désignation :</b> {stock_doc.designation or ''}</li>"
		f"  <li><b>Article :</b> {stock_doc.article or ''}</li>"
		f"  <li><b>Événement :</b> {event.event}</li>"
		f"  <li><b>Date d'échéance :</b> {formatdate(event.event_date)}</li>"
		f"  <li><b>Jours restants :</b> {days_until}</li>"
		f"</ul>"
		f"<p>Merci de prendre les dispositions nécessaires.</p>"
	)

	for recipient in recipients:
		if not frappe.db.exists("User", recipient):
			frappe.logger().warning(f"send_notification : utilisateur {recipient} introuvable")
			continue

		try:
			notification = frappe.get_doc(
				{
					"doctype": "Notification Log",
					"for_user": recipient,
					"type": "Alert",
					"document_type": "Stock",
					"document_name": stock_doc.name,
					"subject": subject,
					"email_content": message,
				}
			).insert(ignore_permissions=True)

			# ✅ Commit par notification pour être sûr qu'elle survit
			#    même si un doc suivant plante et déclenche un rollback
			frappe.db.commit()

			# Publication temps réel pour mettre à jour la cloche
			frappe.publish_realtime(
				event="notification",
				message=notification.as_dict(),
				user=recipient,
				after_commit=True,
			)

		except Exception as exc:
			frappe.logger().error(f"Notification failed for {recipient}: {exc}")
			frappe.db.rollback()
