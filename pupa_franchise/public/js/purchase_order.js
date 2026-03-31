frappe.ui.form.on("Purchase Order", {
    onload: function (frm) {
        if (frm.is_new()) {
            frappe.call({
                method: "pupa_franchise.utils.py.purchase_order.get_purchase_order_credentials",
                args: {
                    company: frm.doc.company
                },
                callback: function (r) {
                    if (r.message.status_1 == "success") {
                        frm.set_value("custom_branch", r.message.response_1);
                    }
                    else {
                        frappe.msgprint({
                            title: "Branch",
                            message: r.message.response_1,
                            indicator: "orange"
                        })
                    }
                    if (r.message.status_2 == "success") {
                        frm.set_value("supplier", r.message.response_2);
                    } else {
                        frappe.msgprint({
                            title: "Supplier",
                            message: r.message.response_2,
                            indicator: "orange"
                        })
                    }

                }
            })
        }
    },
    custom_branch: function (frm) {
        if (!frm.doc.custom_branch) return;

        (frm.doc.items || []).forEach(row => {
            if (row.item_code) {
                get_stock_from_pupa(frm, row.doctype, row.name);
            }
        })
    },
    company: function (frm) {
        if (frm.doc.company) {
            console.log("hi");
            
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Company",
                    filters: { name: frm.doc.company },
                    fieldname: ["custom_branch"]
                },
                callback: function (r) {
                    if (r.message.custom_branch) {
                        // frappe.msgprint(r.message.custom_branch)
                        frm.set_value("custom_branch", r.message.custom_branch);
                    } else {
                        frappe.msgprint("Branch not mapped in Company")
                        frm.set_value("custom_branch", "");
                    }
                }
            });
        }
    }
})

frappe.ui.form.on("Purchase Order Item", {
    item_code: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code) {
            get_stock_from_pupa(frm, cdt, cdn);
        } else {
            frappe.model.set_value(cdt, cdn, "custom_available_qty_in_pupa", "")
        }
    }
})

function get_stock_from_pupa(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    frappe.call({
        method: "pupa_franchise.api.api_sync.get_stock_from_pupa",
        args: {
            branch: frm.doc.custom_branch
        },
        callback: function (r) {
            if (r.message) {
                let stock = r.message.find(d => d.item_code === row.item_code);
                if (stock) {
                    row.custom_available_qty_in_pupa = stock.actual_qty
                    frm.refresh_field("items");
                }
                else {
                    console.log("No stock for item:", row.item_code);
                }
            }
        }
    })
}