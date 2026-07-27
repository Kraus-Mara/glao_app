// Copyright (c) 2026, Frappe Technologies and contributors
// For license information, please see license.txt


frappe.ui.form.on("Creation DMC", {
    project(frm) {
		frm.call("_get_contact_from_project").then(({message: contacts}) => {
			const data = contacts.map(contact => ({
				value: contact.name,
				label: contact.name
			}));
			frm.fields_dict.contact.set_data(data);
		})
    },
});
