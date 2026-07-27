// Copyright (c) 2026, Frappe Technologies and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Article", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Characteristics", {
    characteristics_type(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.characteristics_type) return;
        frm.call({
            method: "get_units",
            doc: frm.doc,
            args: { char_type: row.characteristics_type },
            callback(r) {
                if (!r.message) return;
                const data = r.message.map((s) => ({
                    value: s.unit,
                    label: s.unit,
                }));
                const grid_row = frm.fields_dict["chars"].grid.grid_rows_by_docname[cdn];
                if (grid_row) {
                    grid_row.get_field("unit").set_data(data);
                }
            },
        });
    },
});

frappe.ui.form.on("Article", {
	refresh_table(frm) {
		if (frm.is_new()) return;

		frm.call({
			method: "_fetch_place_rules",
			doc: frm.doc,
			freeze: true,
			freeze_message: __("Chargement des règles..."),
			callback(r) {
				if (!r.message) return;
				frm.clear_table("place_rules");

				let total_minimum = 0;
				let total_maximum = 0;
				let total_expected = 0;
				r.message.forEach((row) => {
					let child = frm.add_child("place_rules");
					child.place = row.parent;
					child.hidden_place_rules = row.name;
					child.minimum_quantity = row.minimum_quantity || 0;
					child.expected_quantity = row.expected_quantity || 0;
					child.maximum_quantity = row.maximum_quantity || 0;

					total_minimum += flt(row.minimum_quantity);
					total_maximum += flt(row.maximum_quantity);
					total_expected += flt(row.expected_quantity);
				});
				frm.set_value("total_minimum", total_minimum);
				frm.set_value("total_maximum", total_maximum);
				frm.set_value("total_expected", total_expected);
				frm.refresh_field("place_rules");
			},
		});
	},
});
