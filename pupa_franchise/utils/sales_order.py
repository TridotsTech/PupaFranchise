import frappe
from frappe.utils import flt, today


def on_submit(doc, method):
    create_pi_for_influencer_so(doc.name)



@frappe.whitelist()
def create_pi_for_influencer_so(so_name):
    so = frappe.get_doc("Sales Order", so_name)

    if not so.custom_do_you_have_any_influencer:
        return 

    influencer_rows = so.get("custom_influencer_discount_details")

    if not influencer_rows:
        frappe.msgprint("No influencer discount details found.", alert=True)
        return

    created_invoices = []

    for row in influencer_rows:
        if not row.employee or not row.discount_percent:
            continue

        supplier_name = get_or_create_supplier_from_employee(row.employee)
        discount_prct = flt(row.discount_percent)
        grand_total = flt(so.grand_total)
        discounted_amount = grand_total - (grand_total * discount_prct) / 100

        pi_items = []
        for item in so.items:
            item_rate = flt(item.rate)
            discounted_rate = item_rate - (item_rate * discount_prct) / 100

            pi_items.append({
                "doctype": "Purchase Invoice Item",
                "item_code": item.item_code,
                "item_name": item.item_name,
                "description": item.description or item.item_name,
                "qty": flt(item.qty),
                "uom": item.uom,
                "rate": discounted_rate,
                "amount": discounted_rate * flt(item.qty),
                "cost_center": frappe.db.get_value(
                    "Company", so.company, "cost_center"
                ),
            })

        pi = frappe.new_doc("Purchase Invoice")
        pi.supplier = supplier_name
        pi.company = so.company
        pi.posting_date = frappe.utils.today()
        pi.due_date = frappe.utils.today()
        pi.currency = so.currency
        pi.buying_price_list = "Standard Buying"
        pi.custom_sales_order = so_name 
        pi.set("items", pi_items)
        pi.insert(ignore_permissions=True)

        created_invoices.append(pi.name)

        frappe.msgprint(
            f"Purchase Invoice <b>{pi.name}</b> created for Supplier <b>{supplier_name}</b> "
            f"with {discount_prct}% discount (Amount: {discounted_amount}).",
            alert=True
        )

    return created_invoices


def get_or_create_supplier_from_employee(emp_id):
    employee = frappe.get_doc("Employee", emp_id)
    emp_name = employee.employee_name

    existing_supplier = frappe.db.get_value(
        "Supplier",
        {"supplier_name": emp_name},
        "name"
    )

    if existing_supplier:
        return existing_supplier

    supplier = frappe.new_doc("Supplier")
    supplier.supplier_name = emp_name
    supplier.supplier_group = frappe.db.get_single_value("Buying Settings", "supplier_group") or "All Supplier Groups"
    supplier.supplier_type = "Individual"
    supplier.custom_employee = emp_id
    supplier.insert(ignore_permissions=True)
    frappe.db.commit()

    frappe.msgprint(
        f"New Supplier <b>{emp_name}</b> created automatically.",
        alert=True
    )

    return supplier.name

