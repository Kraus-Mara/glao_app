// Copyright (c) 2026, Frappe Technologies and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Stock", {
//  refresh(frm) {

//  },
// });
frappe.ui.form.on("Stock", {
    refresh(frm) {
        frm.fields_dict.events.grid.wrapper.find(".grid-row").each(function(i, row) {
            const data = frm.doc.events[i];
            if (!data) return;
            if (data.event === "DLU" && frappe.datetime.get_diff(data.event_date, frappe.datetime.nowdate()) < 0) {
                $(row).css("background-color", "#ffd5d5");
            }
        });
    }
});

frappe.ui.form.on("Stock", {
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
