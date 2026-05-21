// Copyright (c) 2026, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.treeview_settings["Places"] = {
    breadcrumb: "Places",
    title: "Places Tree Structure",

    filters: [
    ],

    onload: function(treeview) {
        frappe.after_ajax(function() {
            treeview.tree && treeview.tree.load_children(treeview.tree.root_node, true);
        });
    },

    fields: [
        {
            fieldtype: "Data",
            fieldname: "place_name",
            label: "Place name",
            reqd: true,
        },
        {
            fieldtype: "Check",
            fieldname: "is_group",
            label: "Is group",
        },
        {
            fieldtype: "Check",
            fieldname: "is_active",
            label: "is Active",
            hidden: true,
            default: 1,
        },
        {
            fieldtype: "Check",
            fieldname: "address",
            label: "Has an address",
            default: 0,
        },
        {
            fieldtype: "Data",
            fieldname: "location",
            label: "Location",
        },
        {
            fieldtype: "Link",
            fieldname: "company",
            options: "Company",
            label: "Company",
        },
        {
            fieldtype: "Check",
            fieldname: "external",
            label: "Is external",
        }
    ],
};
