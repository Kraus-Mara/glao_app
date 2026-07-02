// Copyright (c) 2026, Frappe Technologies and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Article", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Characteristics", {
    characteristics_type(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.characteristics_type) return;
        frm.call({
            method: "get_units",
            doc: frm.doc,
            args: { char_type: row.characteristics_type },
            callback(r) {
                if (!r.message) return;
                const data = r.message.map((s) => ({
                    value: s.unit,
                    label: s.unit,
                }));
                const grid_row = frm.fields_dict["chars"].grid.grid_rows_by_docname[cdn];
                if (grid_row) {
                    grid_row.get_field("unit").set_data(data);
                }
            },
        });
    },
});

