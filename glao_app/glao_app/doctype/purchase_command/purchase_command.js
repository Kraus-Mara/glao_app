// Copyright (c) 2026, kr and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Command', {
    refresh: function(frm) {
        frm.set_query('supplier', 'items', function(doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            if (row.article) {
                return {
                    filters: {
                        'parent': row.article
                    }
                };
            }
            return {};
        });
    }
});
