// Copyright (c) 2026, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Movement", {
    article_from_stock(frm) {
        if (frm.doc.article_from_stock) {
            frm.call("scrap_sources").then(({message: sources}) => {
                const data = sources.map(path => ({
                    value: path.split("/").pop(),
                    label: path
                }));
                frm.fields_dict.source_place.set_data(data);
            })
        }
    },
});

