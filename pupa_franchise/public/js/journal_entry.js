frappe.ui.form.on("Journal Entry", {
    refresh(frm) {
        frm.set_query("custom_trade_discount_party_type", function () {
            return {
                filters: {
                    name: ["in", ["Customer"]],
                },
            };
        });
    },
    onload(frm) {
        frm.set_query("custom_trade_discount_party_type", function () {
            return {
                filters: {
                    name: ["in", ["Customer"]],
                },
            };
        });
    },
    voucher_type(frm) {
        if (frm.doc.voucher_type === "Trade Discount") {
            frappe.call({
                method: "pupa_franchise.pupa_franchise.utils.py.journal_entry.trade_discount",
                args: { doc: frm.doc },
                callback: function (r) {
                    if (r.message) {
                        frm.clear_table("accounts");
                        if (r.message.debtors_account) {
                            let row = frm.add_child("accounts");
                            row.account = r.message.debtors_account;
                            row.party_type = "Customer";
                            row.reference_type = "Sales Invoice";
                        }
                        if (r.message.trade_account) {
                            let row = frm.add_child("accounts");
                            row.account = r.message.trade_account;
                        }
                        frm.refresh_field("accounts");
                    }
                }
            });
        }
    },
    custom_trade_party: function(frm) {
        if (frm.doc.voucher_type === "Trade Discount") {
            frappe.call({
                method: "pupa_franchise.pupa_franchise.utils.py.journal_entry.outstanding_ledger_details",
                args: { doc: frm.doc },
                callback: function(r) {
                    if (r.message && r.message.outstanding) {
                        frm.clear_table("accounts");
                        let total_outstanding = 0;
                        $.each(r.message.outstanding, function(i, ledger) {
                            let row = frm.add_child("accounts");
                            row.account = ledger.account;
                            row.party_type = "Customer";
                            row.party = frm.doc.custom_trade_party;
                            row.reference_type = ledger.voucher_type;
                            row.reference_name = ledger.voucher_no;
                            row.reference_due_date = ledger.due_date;
                            row.credit_in_account_currency = 0;
                            row.custom_outstanding_amount = ledger.outstanding_amount;

                            total_outstanding += ledger.outstanding_amount;
                        });
                        if (r.message.trade_account) {
                            let discount_row = frm.add_child("accounts");
                            discount_row.account = r.message.trade_account;
                            discount_row.debit_in_account_currency = 0;
                        }
                        frm.refresh_field("accounts");
                    }
                }
            });
        }
    }
});
