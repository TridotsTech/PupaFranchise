import frappe

@frappe.whitelist()
def get_purchase_order_credentials(company=None):
    if not company:
        return

    branch_name = frappe.db.get_value("Company", company, "custom_branch")
    supplier = frappe.db.get_single_value("Franchise Settings", "default_supplier")

    response = {}

    if branch_name:
        response["response_1"] = branch_name
        response["status_1"] = "success"
    else:
        response["response_1"] = "Branch is not mapped in company"
        response["status_1"] = "failure"

    if supplier:
        response["response_2"] = supplier
        response["status_2"] = "success"
    else:
        response["response_2"] = "Default supplier is not mapped in Pupa Settings!"
        response["status_2"] = "failure"
    
    return response