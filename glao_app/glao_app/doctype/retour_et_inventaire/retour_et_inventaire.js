// Copyright (c) 2026, kr and contributors
// For license information, please see license.txt

frappe.ui.form.on('Retour et Inventaire', {
    refresh(frm) {
        apply_row_styles(frm, 'sent_items');
        apply_row_styles(frm, 'sent_compositions');
    },
    sent_items_add(frm) { setTimeout(() => apply_row_styles(frm, 'sent_items'), 100); },
    sent_items_remove(frm) { setTimeout(() => apply_row_styles(frm, 'sent_items'), 100); },
    sent_compositions_add(frm) { setTimeout(() => apply_row_styles(frm, 'sent_compositions'), 100); },
    sent_compositions_remove(frm) { setTimeout(() => apply_row_styles(frm, 'sent_compositions'), 100); },
});

frappe.ui.form.on("Retour Items", {
    quantity: (frm, cdt, cdn) => suggest_places_to_stock(frm, cdt, cdn),
    reason:   (frm, cdt, cdn) => suggest_places_to_stock(frm, cdt, cdn),
    item(frm, cdt, cdn) { setTimeout(() => apply_row_styles(frm, cdt.includes("sent_items") ? 'sent_items' : 'sent_compositions'), 50); }
});

frappe.ui.form.on("Retour Compos", {
    quantity: (frm, cdt, cdn) => suggest_places_to_stock(frm, cdt, cdn),
    reason:   (frm, cdt, cdn) => suggest_places_to_stock(frm, cdt, cdn),
    item(frm, cdt, cdn) { setTimeout(() => apply_row_styles(frm, 'sent_compositions'), 50); }
});

/**
 * Applique gras sur STM-C + indentation sur is_sub_item
 */
function apply_row_styles(frm, table_fieldname) {
    const grid = frm.fields_dict[table_fieldname]?.grid;
    if (!grid) return;

    // On parcourt les lignes du DOM
    const rows = grid.wrapper.find('.grid-row');
    rows.each(function () {
        const $row = $(this);
        const row_name = $row.attr('data-name');
        const doc = grid.grid_rows_by_docname?.[row_name]?.doc
                 || (grid.get_row(row_name) || {}).doc;
        if (!doc) return;

        const isStmC     = String(doc.item || doc.article || '').startsWith('STM-C');
        const isSubItem  = cint(doc.is_sub_item) === 1;

        // Reset
        $row.find('[data-fieldname="item"], [data-fieldname="article"]')
            .css({ 'font-weight': '', 'padding-left': '', 'position': 'relative' })
            .removeClass('stm-c-bold sub-item-indent');

        // Gras sur les STM-C
        if (isStmC) {
            $row.find('[data-fieldname="item"], [data-fieldname="article"]')
                .addClass('stm-c-bold')
                .css('font-weight', '700');
        }

        // Indentation des sous-articles
        if (isSubItem) {
            const $cell = $row.find('[data-fieldname="item"], [data-fieldname="article"]');
            $cell.addClass('sub-item-indent').css({
                'padding-left': '28px',
                'position': 'relative'
            });
            // Petit chevron ↳ pour la lisibilité
            if (!$cell.find('.sub-arrow').length) {
                $cell.prepend('<span class="sub-arrow" style="position:absolute;left:8px;color:#8d99a6;">↳</span>');
            }
        }
    });
}

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
                grid_row.refresh_field("place_to_stock");
            }
        }
    });
}
