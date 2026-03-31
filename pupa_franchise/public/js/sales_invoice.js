frappe.ui.form.on('Sales Team', {
    sales_person: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.sales_person) {
            frappe.call({
                method: "pupa_franchise.api.sales_invoice.get_sales_person_mobile",
                args: {
                    sales_person: row.sales_person
                },
                callback: function(r) {
                    if (r.message.status === "success") {
                        frappe.model.set_value(cdt, cdn, "custom_mobile_number", r.message.mobile_number);
                    } else {
                        frappe.msgprint(r.message.message);
                    }
                }
            });
        }
    }
});