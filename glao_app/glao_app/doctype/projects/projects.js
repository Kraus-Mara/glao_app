// Copyright (c) 2026, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Projects", {
    end_date(frm) {
        if (frm.doc.end_date) {
            if (frm.doc.starting_date > frm.doc.end_date) {
                frappe.msgprint(`La date de fin se trouve avant la date de début`);
                frm.set_value(`end_date`, null)
            }
        }
    }
});
