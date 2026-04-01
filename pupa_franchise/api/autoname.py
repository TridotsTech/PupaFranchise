import frappe
from datetime import datetime
from frappe.model.naming import make_autoname, revert_series_if_last
from erpnext.accounts.utils import get_fiscal_year


def naming_series_creation(doc, method):
    if not doc.company:
        return
    
    doctype = doc.doctype

    date_field = doc.transaction_date if doc.doctype in [
        "Sales Order", "Purchase Order"
    ] else doc.posting_date

    fy_year = get_fiscal_year(date_field, as_dict=True) if date_field else None

    if not fy_year:
        return

    start_year = str(fy_year["year_start_date"].year)[-2:]
    end_year = str(fy_year["year_end_date"].year)[-2:]
    fiscal_suffix = f"{start_year}{end_year}"
    frappe.log_error("FISCAL YR SUFFIX", fiscal_suffix)

    series = None
        
    if doctype == "Sales Invoice":
        if hasattr(doc, "is_return") and doc.is_return:
            series = f"CN-{fiscal_suffix}-.####"
        else:
            series = f"HT-{fiscal_suffix}-.####"

    if doctype == "Payment Entry":
        if hasattr(doc, "party_type") and doc.party_type == "Customer":
            series = f"RE-{fiscal_suffix}-.####"
        elif hasattr(doc, "party_type") and doc.party_type == "Supplier":
            series = f"PA-{fiscal_suffix}-.####"
        else:
            series = None

    if doctype == "Purchase Invoice":
        if hasattr(doc, "is_return") and doc.is_return:
            series = f"DN-{fiscal_suffix}-.####"
        else:
            series = f"PI-{fiscal_suffix}-.####"

    if doctype == "Journal Entry":
        if hasattr(doc, "voucher_type") and doc.voucher_type == "Trade Discount":
            series = f"TD-{fiscal_suffix}-.####"
        else:
            series = f"JN-{fiscal_suffix}-.####"

    if doctype == "Stock Entry":
        series = f"SE-{fiscal_suffix}-.####"

    if doctype == "Purchase Order":
        series = f"PO-{fiscal_suffix}-.####"

    if doctype == "Sales Order":
        series = f"SO-{fiscal_suffix}-.####"

    if series:
        doc.name = make_autoname(series)

