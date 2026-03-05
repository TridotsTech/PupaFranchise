frappe.ui.form.on("Purchase Order", {
    supplier: function (frm) {
        if (!frm.doc.supplier) return;

        (frm.doc.items || []).forEach(row => {
            if (row.item_code) {
                get_stock_from_pupa(frm, row.doctype, row.name);
            }
        })
    }
})

frappe.ui.form.on("Purchase Order Item", {
    item_code: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!frm.doc.supplier) {
            frappe.msgprint({
                title: __("Missing Supplier"),
                message: __("Please select Supplier before selecting Item."),
                indicator: "orange"
            });
            return;
        }

        if (row.item_code) {
            get_stock_from_pupa(frm, cdt, cdn);
        }
    }
})

function get_stock_from_pupa(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    frappe.call({
        method: "pupa_franchise.api.api_sync.get_stock_from_pupa",
        args: {
            supplier: frm.doc.supplier
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