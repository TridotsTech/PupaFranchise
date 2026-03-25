frappe.ui.form.on('Sales Invoice', {
    refresh(frm) {
        if (frm.doc.docstatus === 1 && frm.doc.custom_message_status === "Not Sent") {
            frm.add_custom_button(__('Send WhatsApp'), function() {
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
