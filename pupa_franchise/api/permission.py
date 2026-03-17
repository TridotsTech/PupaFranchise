import frappe

def get_permission_query_conditions(user, doctype=None):
    if not user:
        user = frappe.session.user

    if not doctype:
        doctype = frappe.flags.current_doctype
    
    if not doctype:
        return ""

    if user == "Administrator" or "System Manager" in frappe.get_roles(user):
        return ""

    allowed_companies = frappe.permissions.get_user_permissions(user).get("Company", [])
    if not allowed_companies:
        return ""

    company_list = [d.get("doc") for d in allowed_companies]
    if not company_list:
        return ""

    meta = frappe.get_meta(doctype)
    
    # Handle Bin specially as it filters by warehouse's company
    if doctype == "Bin":
        companies_str = ", ".join([frappe.db.escape(c) for c in company_list])
        return f"`tabBin`.warehouse IN (SELECT name FROM tabWarehouse WHERE company IN ({companies_str}))"

    # Handle Customer: filter by Allowed Companies child table
    if doctype == "Customer":
        companies_str = ", ".join([frappe.db.escape(c) for c in company_list])
        return (
            f"`tabCustomer`.name IN ("
            f"SELECT parent FROM `tabAllowed Company User Table`"
            f" WHERE parenttype='Customer' AND company IN ({companies_str})"
            f")"
        )

    # Handle Item Price: strict company filter — blank custom_company is hidden from company users
    if doctype == "Item Price":
        companies_str = ", ".join([frappe.db.escape(c) for c in company_list])
        return f"`tabItem Price`.custom_company IN ({companies_str})"

    if meta.has_field("company"):
        companies_str = ", ".join([frappe.db.escape(c) for c in company_list])
        return f"`tab{doctype}`.company IN ({companies_str})"

    return ""

def has_permission(doc, ptype, user):
    if user == "Administrator" or "System Manager" in frappe.get_roles(user):
        return True
    
    allowed_companies = frappe.permissions.get_user_permissions(user).get("Company", [])
    if not allowed_companies:
        return True
        
    company_list = [d.get("doc") for d in allowed_companies]
    
    # Handle Customer: check Allowed Companies child table
    if doc.doctype == "Customer":
        allowed = [row.company for row in doc.get("custom_allowed_companies", [])]
        if not allowed or not any(c in allowed for c in company_list):
            return False
        return True

    # Handle Item Price: strict check — blank or mismatched custom_company is denied
    if doc.doctype == "Item Price":
        if not doc.custom_company or doc.custom_company not in company_list:
            return False
        return True

    if hasattr(doc, "company") and doc.company not in company_list:
        return False
        
    if doc.doctype == "Bin":
        warehouse_company = frappe.db.get_value("Warehouse", doc.warehouse, "company")
        if warehouse_company not in company_list:
            return False

    return True
