// Copyright (c) 2026, kr and contributors
// For license information, please see license.txt

frappe.ui.form.on("Gestion DMC Items", {
    item_from_stock(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.item_from_stock) return;
        frm.call({
            method: "get_source_places",
            doc: frm.doc,
            args: { item_from_stock: row.item_from_stock },
            callback(r) {
                if (!r.message) return;
                const data = r.message.map((s) => ({
                    value: s.place,
                    label: `${s.place} (${s.quantity} disponible(s))`,
                }));
                // const grid_row = frm.fields_dict["gestion_items"].grid.get_row(cdn);
                const grid_row = frm.fields_dict["gestion_items"].grid.grid_rows_by_docname[cdn];
                if (grid_row) {
                    grid_row.get_field("source_place").set_data(data);
                }
            },
        });
    },
    // article(frm, cdt, cdn) {
    //     const row = locals[cdt][cdn];
    //     if (!row.article) return;
    //     frm.call({
    //         method: "get_items_and_substitutes",
    //         doc: frm.doc,
    //         args: { item_asked: row.article },
    //
    //         callback(r) {
    //             if (!r.message) return;
    //             const data = r.message.map((s) => ({
    //                 value: s.name,
    //                 label: s.name,
    //             }));
    //             const grid_row = frm.fields_dict["gestion_items"].grid.grid_rows_by_docname[cdn];
    //             if (grid_row) {
    //                 grid_row.get_field("item_from_stock").set_data(data);
    //             }
    //         }
    //     }).then(({message: items}) => {
    //             const data = items.map(item => ({
    //                 value: item.name,
    //                 // label: `${item.name} - ${item.designation} - (${item.quantity} disponible(s))`
    //                 label: item.name
    //             }));
    //             frm.fields_dict.item_from_stock.set_data(data);
    //     });
    // },

});


// frappe.ui.form.on("Gestion DMC", {
//     refresh(frm) {
//         frm.fields_dict["gestion_items"].grid.wrapper.on("change", () => {}); // force render
//         setTimeout(() => {
//             (frm.doc.gestion_items || []).forEach((row) => {
//                 if (!row.article) return;
//                 frm.call({
//                     method: "get_items_and_substitutes",
//                     doc: frm.doc,
//                     args: { item_asked: row.article },
//                     callback(r) {
//                         if (!r.message) return;
//                         const data = r.message.map((s) => s.name);
//                         console.log(data)
//                         const grid = frm.fields_dict["gestion_items"].grid;
//                         // console.log(grid)
//                         const df = grid.get_docfield("item_from_stock");
//                         console.log(df)
//                         field.df.options = data.map(d => d.value).join("\n");
//                         if (field.input) {
//                             field.set_data(data);
//                         }
                        // df.options = data.join("\n");
                        // const grid_row = frm.fields_dict["gestion_items"].grid.grid_rows_by_docname[row.name];
                        // if (grid_row) {
                        //     grid_row.toggle_view(true, () => {
                        //         const field = grid_row.get_field("item_from_stock");
                        //         field.df.options = data.map(d => d.value).join("\n");
                        //         if (field.input) {
                        //             field.set_data(data);
                        //         }
                        //     });
                        // }
//                     }
//                 });
//             });
//         }, 500);
//     },
// });

