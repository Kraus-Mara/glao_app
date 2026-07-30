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
                            fields: ["name", "designation", "article"],
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
                        let available_lines = Object.values(global_stock_pool)
                            .filter(s => s.article === nom_item.item && s.remaining_qty > 0);

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
                                __("Insufficient Stock available"),
								__(`Article {0} ({1}) : missing quantity is {2}`, [nom_item.designation, nom_item.item, required_qty])
                            );
                        }
                    }

                    if (missing_items_messages.length > 0) {
                        frappe.msgprint({
                            title: __("Insufficient Stock available"),
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
						label: __(`${s.place} (${s.quantity} available)`),
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

