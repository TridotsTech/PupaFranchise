import frappe
import json
from erpnext.accounts.utils import get_outstanding_invoices

def debit_credit_zerorows_delete(doc, method=None):
    if doc.voucher_type == "Trade Discount":
        if doc.accounts:
            for acc_row in doc.accounts[:]:
                if (
                    (acc_row.debit_in_account_currency == 0 or acc_row.debit_in_account_currency is None)
                    and (acc_row.credit_in_account_currency == 0 or acc_row.credit_in_account_currency is None)
                ):
                    doc.remove(acc_row)

@frappe.whitelist()
def trade_discount(doc):
    doc = json.loads(doc)
    if doc.get("voucher_type") == "Trade Discount":
        abbr = frappe.db.get_value("Company", doc.get("company"), "abbr")
        trade_acc = f"Trade Discount - {abbr}"
        deb_acc = f"Debtors - {abbr}"
        trade_acc_exists = frappe.db.exists("Account", trade_acc)
        deb_acc_exists = frappe.db.exists("Account", deb_acc)
        response = {}
        if trade_acc_exists:
            response["trade_account"] = trade_acc
        if deb_acc_exists:
            response["debtors_account"] = deb_acc
        return response 

@frappe.whitelist()
def outstanding_ledger_details(doc):
    doc = json.loads(doc)
    response = {}
    if doc.get("custom_trade_discount_party_type") == "Customer" and doc.get("custom_trade_party"):
        account = frappe.db.get_value(
            "Company",
            doc.get("company"),
            "default_receivable_account"
        )
        account_list = [account]
        outstanding = get_outstanding_invoices(
            party_type="Customer",
            party=doc.get("custom_trade_party"),
            account=account_list
        ) or []
        response["outstanding"] = outstanding
    if doc.get("voucher_type") == "Trade Discount":
        abbr = frappe.db.get_value("Company", doc.get("company"), "abbr")
        trade_acc = f"Trade Discount - {abbr}"
        if frappe.db.exists("Account", trade_acc):
            response["trade_account"] = trade_acc
    return response
