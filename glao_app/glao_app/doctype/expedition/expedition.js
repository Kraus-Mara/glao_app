// Copyright (c) 2026, kr and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Expedition", {
// 	refresh(frm) {

// 	},
// });
//
frappe.ui.form.on("Expedition", {
    print_lof(frm) {
	if (frm.doc.status != "Shipped") return;
        window.open(
            frappe.urllib.get_full_url(
                `/api/method/glao_app.glao_app.doctype.expedition.expedition.export_expedition_excel?name=${encodeURIComponent(frm.doc.name)}`
            )
        );
    },
});
