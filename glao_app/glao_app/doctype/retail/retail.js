// Copyright (c) 2026, kr and contributors
// For license information, please see license.txt

frappe.ui.form.on("Retail", {
    refresh(frm) {
		frm.call("_get_article_to_retail").then(({message: articles}) => {
			const data = articles.map(item => ({
				value: item.designation,
				label: `${item.designation} : ${item.quantity} will be convert to ${item.place} `
			}));
			frm.fields_dict.article_to_retail.set_data(data);
		})
    },
});
