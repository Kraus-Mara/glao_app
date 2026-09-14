// Copyright (c) 2026, kr and contributors
// For license information, please see license.txt
//

frappe.ui.form.on("Retail", {
    article_to_retail(frm) {
        if (frm.doc.article_to_retail) {
            frm.call("scrap_sources").then(({message: sources}) => {
                const data = sources.map(item => ({
                    value: item.place,
                    label: `${item.place} (${item.quantity} disponible(s))`
                }));
                frm.fields_dict.source_place.set_data(data);
            })
        }
    },
});
