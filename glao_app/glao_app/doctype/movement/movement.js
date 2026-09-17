// Copyright (c) 2026, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Movement", {
    article_from_stock(frm) {
        if (frm.doc.article_from_stock) {
            frm.call("scrap_sources").then(({message: sources}) => {
                const data = sources.map(item => ({
                    value: item.place,
                    label: `${item.place} (${item.quantity} disponible(s))`
                }));
                frm.fields_dict.source_place.set_data(data);
            })
        }
    },
    article_to_register(frm) {
        if (frm.doc.article_to_register) {
            frm.call("scrap_sources").then(({message: sources}) => {
                const data = sources.map(item => ({
                    value: item.place,
                    label: `${item.place} (${item.quantity} disponible(s))`
                }));
                frm.fields_dict.source_place.set_data(data);
            });
        }
    },
    article(frm) {
        frm._places_cache = null;
        frm._places_priority = null;

        if (!frm.doc.article) return;

        frm.call({
            method: "get_target_places",
            doc: frm.doc,
            args: { item: frm.doc.article },
            callback(r) {
                if (!r.message) return;
                frm._places_cache = r.message;
                frm._places_priority = r.message
                    .filter(p => p.quantity != null)
                    .map(p => p.place);
            }
        });
    },
    onload_post_render(frm) {
        if (frm.doc.article && !frm._places_cache) {
            frm.trigger("article");
        }
    },
});

frappe.ui.form.on("Places Stock", {
    form_render(frm, cdt, cdn) {
        setTimeout(() => apply_places_data(frm, cdt, cdn), 200);
    },
    placetostock_add(frm, cdt, cdn) {
        setTimeout(() => apply_places_data(frm, cdt, cdn), 300);
    },
});

function apply_places_data(frm, cdt, cdn) {
    if (!frm._places_cache || !frm._places_cache.length) {
        return;
    }
    const grid = frm.fields_dict["placetostock"]?.grid;
    if (!grid) return;
    const grid_row = grid.grid_rows_by_docname[cdn];
    if (!grid_row) return;
    const field = grid_row.get_field("place");
    if (!field) return;

    const data = frm._places_cache.map(p => ({
        value: p.place,
        label: p.quantity != null
            ? `${p.place} (${p.quantity} dispo)`
            : p.place
    }));

    if (field.awesomplete) {
        field.awesomplete.list = [];
    }
    field.set_data(data);
}
