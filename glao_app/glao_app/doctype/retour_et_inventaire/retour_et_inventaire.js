// Copyright (c) 2026, kr and contributors
// For license information, please see license.txt

frappe.ui.form.on('Retour et Inventaire', {
    refresh: function(frm) {
        apply_bold_styles(frm);
    },
    onload: function(frm) {
        apply_bold_styles(frm);
    },
    sent_items_render: function(frm) {
        apply_bold_styles(frm);
    },
    sent_compositions_render: function(frm) {
        apply_bold_styles(frm);
    }
});

frappe.ui.form.on("Retour Items", {
    quantity: function(frm, cdt, cdn) {
        suggest_places_to_stock(frm, cdt, cdn);
    },
    reason: function(frm, cdt, cdn) {
        suggest_places_to_stock(frm, cdt, cdn);
    }
});

function suggest_places_to_stock(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!row || !row.item) return;
    frm.call({
        method: "get_target_places",
        doc: frm.doc,
        args: { item: row.item, reason: row.reason },
        callback(r) {
            if (!r.message) return;

            const data = r.message.map((place) => ({
                value: place,
                label: place
            }));

            const grid_row = frm.fields_dict["sent_items"].grid.grid_rows_by_docname[cdn];
            if (grid_row) {
                grid_row.get_field("place_to_stock").set_data(data);
                // Force le rafraîchissement du champ spécifique de la ligne
                grid_row.refresh_field("place_to_stock");
            }
        }
    });
}

function apply_bold_styles(frm) {
    // 1. Application du gras dans la table sent_items
    if (frm.fields_dict.sent_items && frm.fields_dict.sent_items.grid) {
        frm.fields_dict.sent_items.grid.wrapper.find('.grid-row[data-name]').each(function() {
            let docname = $(this).attr('data-name');
            let row_data = (frm.doc.sent_items || []).find(r => r.name === docname);
            if (row_data && row_data.is_sub_item === 1) {
                set_row_bold($(this), true);
            } else {
                set_row_bold($(this), false);
            }
        });
    }

    // 2. Application du gras dans la table sent_compositions
    if (frm.fields_dict.sent_compositions && frm.fields_dict.sent_compositions.grid) {
        frm.fields_dict.sent_compositions.grid.wrapper.find('.grid-row[data-name]').each(function() {
            let docname = $(this).attr('data-name');
            let row_data = (frm.doc.sent_compositions || []).find(r => r.name === docname);
            if (row_data && row_data.is_sub_item === 1) {
                set_row_bold($(this), true);
            } else {
                set_row_bold($(this), false);
            }
        });
    }
}

function set_row_bold($row, should_be_bold) {
    let weight = should_be_bold ? 'bold' : 'normal';
    $row.css('font-weight', weight);
    $row.find('input, select, span, .grid-static-col, .static-area').css('font-weight', weight);
}
