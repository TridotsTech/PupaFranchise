frappe.ui.form.on('Sales Team', {
    sales_person: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.sales_person) {
            frappe.call({
                method: "pupa_franchise.api.sales_invoice.get_sales_person_mobile",
                args: {
                    sales_person: row.sales_person
                },
                callback: function (r) {
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

frappe.ui.form.on('Sales Invoice', {
    refresh(frm) {
        if (frm.doc.docstatus === 1 && frm.doc.custom_message_status === "Not Sent") {
            frm.add_custom_button(__('Send WhatsApp'), function () {
                frappe.call({
                    method: 'pupa_franchise.pupa_franchise.utils.py.whatsapp.sales_invoice_whatsapp',
                    args: {
                        'name': frm.doc.name,
                        'doctype': 'Sales Invoice'
                    }
                });
            }).addClass('btn-primary');
        }
    }
});