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
    
    if hasattr(doc, "company") and doc.company not in company_list:
        return False
        
    if doc.doctype == "Bin":
        warehouse_company = frappe.db.get_value("Warehouse", doc.warehouse, "company")
        if warehouse_company not in company_list:
            return False

    return True
