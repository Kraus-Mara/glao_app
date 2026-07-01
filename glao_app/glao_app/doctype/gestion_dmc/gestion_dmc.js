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
});

frappe.ui.form.on("Gestion DMC Compositions", {
    nomenclature(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.nomenclature) return;
        frm.call({
            method: "get_composition_from_nomenclature",
            doc: frm.doc,
            args: { nomenclature: row.nomenclature },
            callback(r) {
                if (!r.message) return;
                const data = r.message.map((s) => ({
                    value: s.composition,
                }));
                const grid_row = frm.fields_dict["compositions_de_dmc"].grid.grid_rows_by_docname[cdn];
                if (grid_row) {
                    grid_row.get_field("composition").set_data(data);
                }
            },
        });
    },
});
frappe.ui.form.on('Gestion DMC', {
    refresh: function(frm) {
        frm.get_field('gestion_items').grid.cannot_delete = true;
        frm.get_field('gestion_items').grid.cannot_sort = true;
        frm.refresh_field('gestion_items');
        frm.get_field('compositions_de_dmc').grid.cannot_delete = true;
        frm.get_field('compositions_de_dmc').grid.cannot_sort = true;
        frm.refresh_field('compositions_de_dmc');
    }
});
