import frappe
import re
from datetime import datetime
from frappe.model.naming import make_autoname, revert_series_if_last  
from erpnext.accounts.utils import get_fiscal_year 


def is_year_string(s):
    """
    Checks if a string segment looks like a year (e.g., '2026' or fiscal year '2627').
    """
    if len(s) != 4:
        return False
    # Check if it starts with '20' (e.g. 2026, 2027)
    if s.startswith("20") and s[2:].isdigit():
        return True
    # Check if it is a fiscal year format 'YY(YY+1)' like '2627'
    if s.isdigit():
        try:
            y1 = int(s[:2])
            y2 = int(s[2:])
            if y2 == (y1 + 1) or y2 == (y1 + 1) % 100:
                return True
        except ValueError:
            pass
    return False


def get_company_naming_series(doc):
    """
    Looks up the naming series defined in the Company's custom child table.
    """
    if not getattr(doc, "company", None):
        return None

    try:
        company_doc = frappe.get_doc("Company", doc.company)
    except frappe.DoesNotExistError:
        return None

    # Dynamically find the child table field name and field names inside it
    child_table_fieldname = None
    doc_type_fieldname = None
    prefix_fieldname = None

    for field in company_doc.meta.fields:
        if field.fieldtype == "Table":
            child_meta = frappe.get_meta(field.options)
            temp_doc_type = None
            temp_prefix = None
            for c_field in child_meta.fields:
                if c_field.fieldtype == "Link" and c_field.options == "DocType":
                    temp_doc_type = c_field.fieldname
                elif c_field.fieldname in ["naming_series_prefix", "naming_series", "prefix", "series_prefix"] or (c_field.fieldtype == "Data" and "naming" in c_field.fieldname and "return" not in c_field.fieldname):
                    temp_prefix = c_field.fieldname
            
            if temp_doc_type:
                child_table_fieldname = field.fieldname
                doc_type_fieldname = temp_doc_type
                if not temp_prefix:
                    for c_field in child_meta.fields:
                        if c_field.fieldtype == "Data":
                            temp_prefix = c_field.fieldname
                            break
                prefix_fieldname = temp_prefix
                break

    if not child_table_fieldname or not doc_type_fieldname or not prefix_fieldname:
        return None

    child_rows = company_doc.get(child_table_fieldname) or []
    if not child_rows:
        return None

    series_prefix = None
    is_return_doc = frappe.cint(doc.get("is_return"))
    for row in child_rows:
        if row.get(doc_type_fieldname) == doc.doctype:
            if is_return_doc:
                if frappe.cint(row.get("is_return")) and row.get("return_naming_series"):
                    series_prefix = row.get("return_naming_series")
                else:
                    return None
            else:
                series_prefix = row.get(prefix_fieldname)
            break

    if not series_prefix:
        return None

    series_prefix = series_prefix.strip()

    if "#" in series_prefix:
        return series_prefix

    digit_match = re.search(r"(\d+)$", series_prefix)
    if digit_match:
        digits = digit_match.group(1)
        if not is_year_string(digits):
            num_digits = len(digits)
            hash_length = max(4, num_digits)
            prefix_without_digits = series_prefix[:-num_digits]
            
            if not prefix_without_digits.endswith("."):
                if prefix_without_digits.endswith("-") or prefix_without_digits.endswith("/"):
                    prefix_without_digits = prefix_without_digits + "."
                else:
                    prefix_without_digits = prefix_without_digits + "-."
            return f"{prefix_without_digits}{'#' * hash_length}"

    if series_prefix.endswith(".") or series_prefix.endswith("-") or series_prefix.endswith("/"):
        if not series_prefix.endswith("."):
            series_prefix = series_prefix + "."
        return f"{series_prefix}####"
    else:
        return f"{series_prefix}-.####"


def naming_series_creation(doc, method):
    if not doc.company:
        return
    
    # Try custom company naming series first
    series = get_company_naming_series(doc)
    if series:
        doc.name = make_autoname(series)
        return

    # Fallback to default logic
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


