// Copyright (c) 2026, kr and contributors
// For license information, please see license.txt
frappe.ui.form.on("Composition", {
    nomenclature(frm) {
        if (!frm.doc.nomenclature) return;
        frappe.db.get_doc("Nomenclature", frm.doc.nomenclature).then(nomenclature_doc => {
            let stock_promises = nomenclature_doc.items.map(nom_item => {
                return frappe.call({
                    method: "frappe.client.get_list",
                    args: {
                        doctype: "Stock",
                        filters: [["Stock", "article", "=", nom_item.item], ["Stock", "not_yet_registered", "=", 0]],
                        fields: ["name", "quantity", "designation"],
                        order_by: "creation asc",
                        limit_page_length: 1,
                    }
                }).then(r => {
                    const stocks = r.message || [];
                    const stock = stocks[0];
                    if (!stock || stock.quantity < nom_item.quantity) {
                        frappe.msgprint({
                            title: __("Stock insuffisant"),
                            message: __(`Article {0} : stock disponible {1}, quantité requise {2}`,
                                [nom_item.item, stock ? stock.quantity : 0, nom_item.quantity]),
                            indicator: "red",
                        });
                        return { blocked: true };
                    }
                    return { item: stock.name, designation: stock.designation, quantity: nom_item.quantity, blocked: false };
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
                    row.designation = r.designation;
                    row.quantity = r.quantity;
                });
                frm.refresh_field("items");
            });
        });
    }
});
