frappe.ui.form.on('Purchase Invoice Item', {
    price_list_rate: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.price_list_rate) {
            frappe.model.set_value(cdt, cdn, 'custom_mrp', row.price_list_rate);
        }
    },
    custom_mrp: function (frm, cdt, cdn) {
        update_rate_based_on_discount(frm, cdt, cdn);
    },
    custom_mrp_discount_percentage: function (frm, cdt, cdn) {
        update_rate_based_on_discount(frm, cdt, cdn);
    }
});

function update_rate_based_on_discount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (frm.doc.is_opening !== "Yes" && row.custom_mrp) {
        let discount_amount = (row.custom_mrp * (row.custom_mrp_discount_percentage || 0)) / 100;
        let discounted_price = row.custom_mrp - discount_amount;

        frappe.model.set_value(cdt, cdn, 'rate', discounted_price);
        frappe.model.set_value(cdt, cdn, 'custom_ts_discount_amount', discount_amount);
    }
}
