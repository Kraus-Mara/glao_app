// Copyright (c) 2026, kr and contributors
// For license information, please see license.txt

frappe.ui.form.on("Retour Items", {
    item(frm, cdt, cdn) {
        suggest_places_to_stock(frm, cdt, cdn);
    },
    sent_items_on_form_render(frm, cdt, cdn) {
        suggest_places_to_stock(frm, cdt, cdn);
    }
});

function suggest_places_to_stock(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!row.item) return;

    frm.call({
        method: "get_target_places",
        doc: frm.doc,
        args: { item: row.item },
        callback(r) {
            if (!r.message) return;

            const data = r.message.map((place) => ({
                value: place,
                label: place
            }));

            const grid_row = frm.fields_dict["sent_items"].grid.grid_rows_by_docname[cdn];
            if (grid_row) {
                grid_row.get_field("place_to_stock").set_data(data);
            }
        }
    });
}
