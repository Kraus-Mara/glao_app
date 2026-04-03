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
