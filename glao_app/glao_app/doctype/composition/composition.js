// Copyright (c) 2026, kr and contributors
// For license information, please see license.txt

frappe.ui.form.on("Composition", {
    nomenclature(frm) {
        if (!frm.doc.nomenclature) return;
        frappe.db.get_list("Places", {
            filters: { litige: 1 },
            fields: ["name"]
        }).then(litigious_places_docs => {
            const litigious_places = new Set(litigious_places_docs.map(p => p.name));
            frappe.db.get_doc("Nomenclature", frm.doc.nomenclature).then(nomenclature_doc => {
                const global_stock_pool = {};
                let stock_requests = nomenclature_doc.items.map(nom_item => {
                    return frappe.call({
                        method: "frappe.client.get_list",
                        args: {
                            doctype: "Stock",
                            filters: [["Stock", "article", "=", nom_item.item], ["Stock", "not_yet_registered", "=", 0]],
                            fields: ["name", "designation", "article", "fabricant_hidden", "ref_constructeur"],
                            order_by: "creation asc"
                        }
                    }).then(r => {
                        const lines = r.message || [];
                        let detail_promises = lines.map(line => {
                            return frappe.db.get_doc("Stock", line.name).then(stock_doc => {
                                (stock_doc.place_table || []).forEach(p_row => {
                                    if (litigious_places.has(p_row.place)) return;
                                    if (flt(p_row.quantity) <= 0) return;
                                    const pool_key = `${stock_doc.name}_${p_row.place}`;
                                    global_stock_pool[pool_key] = {
                                        name: stock_doc.name,
                                        article: stock_doc.article,
                                        designation: stock_doc.designation,
                                        fabricant: stock_doc.fabricant_hidden,
                                        ref_fabricant: stock_doc.ref_constructeur,
                                        place: p_row.place,
                                        remaining_qty: flt(p_row.quantity)
                                    };
                                });
                            });
                        });
                        return Promise.all(detail_promises);
                    });
                });

                Promise.all(stock_requests).then(() => {
                    let final_rows = [];
                    let missing_items_messages = [];

                    for (let nom_item of nomenclature_doc.items) {
                        let required_qty = flt(nom_item.quantity);

                        // Toutes les lignes de stock disponibles pour cet article
                        let available_lines = Object.values(global_stock_pool)
                            .filter(s => s.article === nom_item.item && s.remaining_qty > 0);

                        // Détection : article suivi (SN/BN) ou non
                        const is_serialized = /-(SN|BN)-/.test(nom_item.item || "");

                        if (is_serialized) {
                            // ========== ARTICLE SUIVI ==========
                            // On garde l'éclatement ligne par ligne (chaque série est unique)
                            for (let stock_line of available_lines) {
                                if (required_qty <= 0) break;
                                let take = Math.min(required_qty, stock_line.remaining_qty);

                                final_rows.push({
                                    item: stock_line.name,
                                    designation: stock_line.designation,
                                    quantity: take
                                });
                                stock_line.remaining_qty -= take;
                                required_qty -= take;
                            }

                            if (required_qty > 0) {
                                missing_items_messages.push(
                                    __("Stock insuffisant"),
                                    __("Article {0} ({1}) : quantité manquante : {2}", [nom_item.designation, nom_item.item, required_qty])
                                );
                            }
                        } else {
                            // ========== ARTICLE NON-SUIVI ==========
                            // On calcule la quantité totale disponible, mais on ne crée qu'UNE ligne

                            const total_available = available_lines.reduce(
                                (sum, s) => sum + flt(s.remaining_qty), 0
                            );

                            // Quantité à mettre dans la ligne unique
                            const qty_to_place = required_qty;
                            const qty_missing = Math.max(0, required_qty - total_available);

                            if (total_available <= 0) {
                                // Aucun stock disponible du tout
                                missing_items_messages.push(
                                    __("Stock insuffisant"),
                                    __("Article {0} ({1}) : quantité manquante : {2}", [nom_item.designation, nom_item.item, required_qty])
                                );
                            } else {
                                // Une seule ligne avec la quantité demandée.
                                // Même si le stock total est insuffisant, on met la quantité demandée.
                                // L'utilisateur verra au moment du choix de l'emplacement qu'il faut regrouper.
                                final_rows.push({
                                    item: available_lines[0].name,
                                    designation: available_lines[0].designation,
                                    quantity: qty_to_place
                                });

                                // Si on veut prévenir quand même d'un manque :
                                if (qty_missing > 0) {
                                    frappe.show_alert({
                                        message: __("Attention : quantité disponible ({0}) inférieure à la demande ({1}) pour {2}", [total_available, required_qty, nom_item.designation]),
                                        indicator: "orange"
                                    }, 8);
                                }
                            }
                        }
                    }

                    // Si au moins un article suivi est manquant, on bloque.
                    // Pour les non-suivis, on laisse passer (l'utilisateur gère via saved_place).
                    if (missing_items_messages.length > 0) {
                        frappe.msgprint({
                            title: __("Stock insuffisant"),
                            message: missing_items_messages,
                            indicator: "red",
                            as_list: true
                        });
                        frm.set_value("nomenclature", "");
                        return;
                    }

                    frm.clear_table("items");
                    final_rows.forEach(r => {
                        let row = frm.add_child("items");
                        row.item = r.item;
                        row.designation = r.designation;
                        row.quantity = r.quantity;
                    });
                    frm.refresh_field("items");
                });
            });
        });
    },
    refresh: function(frm) {
        frm.set_df_property('items', 'cannot_add_rows', true);
        frm.set_df_property('items', 'cannot_delete_rows', true);
        frm.set_query('saved_place', 'items', function(doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            if (row.saved_place) return;
            frm.call({
                method: "get_source_places",
                doc: frm.doc,
                args: { item_from_stock: row.item },
                callback(r) {
                    if (!r.message) return;
                    const data = r.message.map((s) => ({
                        value: s.place,
                        label: __("{0} ({1} disponible(s))", [s.place, s.quantity]),
                    }));
                    const grid_row = frm.fields_dict["items"].grid.grid_rows_by_docname[cdn];
                    if (grid_row) {
                        grid_row.get_field("saved_place").set_data(data);
                    }
                },
            });
            return {};
        });
    }
});
