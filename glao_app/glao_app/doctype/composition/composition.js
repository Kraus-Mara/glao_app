// Copyright (c) 2026, kr and contributors
// For license information, please see license.txt

frappe.ui.form.on("Composition", {
    nomenclature(frm) {
        if (!frm.doc.nomenclature) return;

        frappe.db.get_doc("Nomenclature", frm.doc.nomenclature).then(nomenclature_doc => {
            let blocked = false;

            let stock_promises = nomenclature_doc.items.map(nom_item => {
                return frappe.db.get_list("Stock", {
                    filters: { article: nom_item.item },
                    fields: ["name", "quantity"],
                }).then(stocks => {
                    const total_stock = stocks.reduce((sum, s) => sum + s.quantity, 0);
                    if (total_stock < nom_item.quantity) {
                        frappe.msgprint({
                            title: __("Stock insuffisant"),
                            message: __(`Article {0} : stock disponible {1}, quantité requise {2}`,
                                [nom_item.item, total_stock, nom_item.quantity]),
                            indicator: "red",
                        });
                        blocked = true;
                    }
                    return { item: nom_item.item, quantity: nom_item.quantity, blocked };
                });
            });

            Promise.all(stock_promises).then(results => {
                if (results.some(r => r.blocked)) {
                    frm.set_value("nomenclature", "");
                    return;
                }
                frm.clear_table("items");
                results.forEach(r => {
                    let row = frm.add_child("items");
                    row.item = r.item;
                    row.quantity = r.quantity;
                });
                frm.refresh_field("items");
            });
        });
    }
});
