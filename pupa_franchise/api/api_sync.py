from requests import request
import frappe
import json
import requests


@frappe.whitelist()
def get_api_settings():
    settings = frappe.get_doc("Franchise Settings")
    base_url = settings.url
    if settings.headers and len(settings.headers) > 0:
        header_row = settings.headers[0]
        content_type = header_row.content_type
        authorization_token = header_row.authorization_token
    else:
        frappe.throw("Please Configure headers in API Settings")
    
    headers = {
        "Authorization": f"token {authorization_token}",
        "Content-Type": content_type
    }

    return base_url, headers

@frappe.whitelist()
def create_item(item_code=None, item_name=None, item_group=None, stock_uom=None, gst_hsn_code=None):
    frappe.log_error("Func called")
    if not item_code:
        frappe.throw("Item Code is required")

    if not frappe.db.exists("Item", item_code):
        item = frappe.new_doc("Item")
        item.item_code = item_code
        item.item_name = item_name
        item.item_group = item_group
        item.stock_uom = stock_uom
        item.gst_hsn_code = gst_hsn_code
        item.insert(ignore_permissions=True)
        frappe.db.commit()

        return item.name

@frappe.whitelist()
def create_item_group(item_group_name=None, parent_item_group=None, is_group=None):
    frappe.log_error("Func Called IG")

    if not item_group_name:
        frappe.throw("Item Group is Required!")

    if not frappe.db.exists("Item Group", item_group_name):
        item_grp = frappe.new_doc("Item Group")
        item_grp.item_group_name = item_group_name
        item_grp.parent_item_group = parent_item_group
        item_grp.is_group = is_group

        item_grp.insert(ignore_permissions=True)
        frappe.db.commit()

        return item_grp.name


# def create_franchise_supplier_to_pupa_customer(doc, method):
#     try:
#         base_url, headers = get_api_settings()

#         customer_data = {
#             "doctype": "Customer",
#             "customer_name": doc.supplier_name,
#             "customer_type": doc.supplier_type,
#             "customer_group": "Franchise",
#             "territory": doc.country if doc.country else "All Territories"
#         }

#         response = requests.post(
#             f{base_url}/api/resource/Customer,
#             json=customer_data,
#             headers=headers
#         )

#         if response.status_code == 200:
#             frappe.msgprint(
#                 f"Customer '{doc.supplier_name}' Created in Pupa Instance",
#                 indicator="green",
#                 alert=True
#             )

#         else:
#             frappe.log_error(
#                 message=f"Failed to create customer in Pupa.\nStatus: {response.status_code}\nResponse: {response.text}",
#                 title="Franchise Sync Error"
#             )
#             frappe.throw(f"Failed to create customer in Pupa instance. Status: {response.status_code}")

#     except Exception as e:
#          frappe.log_error(
#             message=frappe.get_traceback(),
#             title="Franchise Supplier to Pupa Customer Error"
#         )
#         frappe.throw(f"Error syncing supplier to Pupa: {str(e)}")

def create_franchise_supplier_to_pupa_customer(doc, method):
    try:
        base_url, headers = get_api_settings()

        payload = {
            "customer_name": doc.supplier_name,
            "customer_type": doc.supplier_type,
            "customer_group": "Franchise",
            "territory": doc.country if doc.country else "All Territories"
        }

        create_url = f"{base_url}/api/method/pupa.api.franchise.create_customer"

        response = requests.post(
            url=create_url,
            headers=headers,
            data=json.dumps(payload)
        )

        frappe.log_error("Pupa Customer Sync Response", response.text)

        if response.status_code == 200:
            frappe.msgprint(
                f"Customer '{doc.supplier_name}' Created in Pupa Instance",
                indicator="green",
                alert=True
            )
        else:
            frappe.log_error(
                message=f"Failed to create customer in Pupa.\nStatus: {response.status_code}\nResponse: {response.text}",
                title="Franchise Sync Error"
            )
            frappe.throw(f"Failed to create customer in Pupa instance. Status: {response.status_code}")

    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Franchise Supplier to Pupa Customer Error"
        )
        frappe.throw(f"Error syncing supplier to Pupa: {str(e)}")



def create_so_from_franchise_po(doc, method):
    try:
        settings = frappe.get_single("Franchise Settings")
        base_url, headers = get_api_settings()

        payload = {
            "customer": doc.supplier,
            "company": settings.hq_company,
            "transaction_date": str(doc.transaction_date),
            "delivery_date": str(doc.schedule_date) if doc.schedule_date else str(doc.transaction_date),
            "custom_franchise_po_id": doc.name,
            "items": []
        }

        for item in doc.items:
            payload["items"].append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": item.qty,
                "uom": item.uom,
                "rate": item.rate
            })

        frappe.log_error("SO Payload", payload)

        create_url = f"{base_url}/api/method/pupa.api.franchise.create_sales_order"

        response = requests.post(
            url=create_url,
            headers=headers,
            data=json.dumps(payload)
        )

        frappe.log_error("Pupa PO Sync Response", response.text)

        if response.status_code == 200:
            frappe.msgprint(
                f"Sales Order Created in Pupa Instance against the PO '{doc.name}'",
                indicator="green",
                alert=True
            )

        else:
            frappe.log_error(
                message=f"Failed to create Sales Order in Pupa.\nStatus: {response.status_code}\nResponse: {response.text}",
                title="Franchise PO to Pupa SO Sync Error"
            )
            frappe.throw(f"Failed to create Sales Order in Pupa Instance. Status: {response.status_code}")

    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Franchise PO to Pupa SO Error"
        )
        frappe.throw(f"Error syncing PO to Pupa Sales Order: {str(e)}")
        


@frappe.whitelist()
def create_purchase_receipt(supplier=None, company=None, posting_date=None, custom_sales_invoice_id=None, items=None):
    try:
        frappe.log_error("Create Purchase Receipt Called", f"Supplier: {supplier}, Bill No: {custom_sales_invoice_id}")

        if not supplier:
            frappe.throw("Supplier is required")

        pupa_supplier = frappe.db.get_single_value("Franchise Settings", "default_supplier")
        frappe.log_error("Def Supplier", pupa_supplier)

        if not items:
            frappe.throw("Items are required")

        if isinstance(items, str):
            items = json.loads(items)

        pr = frappe.new_doc("Purchase Receipt")
        pr.supplier = pupa_supplier
        pr.company = company
        pr.posting_date = posting_date
        pr.custom_sales_invoice_id = custom_sales_invoice_id

        for item in items:
            default_warehouse = frappe.db.get_value(
                "Item Default",
                {"parent": item.get("item_code"), "company": company},
                "default_warehouse"
            )

            pr.append("items", {
                "item_code": item.get("item_code"),
                "item_name": item.get("item_name"),
                "qty": item.get("qty"),
                "uom": item.get("uom"),
                "rate": item.get("rate"),
                "amount": item.get("amount"),
                "warehouse": default_warehouse
            })

        pr.flags.ignore_mandatory = True
        pr.insert(ignore_permissions=True)
        # No submit — stays Draft
        frappe.db.commit()

        frappe.log_error("Purchase Receipt Created", pr.name)

        return {"message": pr.name}

    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Create Purchase Receipt Error"
        )
        frappe.throw(f"Error creating Purchase Receipt: {str(e)}")


@frappe.whitelist()
def create_purchase_invoice(supplier=None, company=None, posting_date=None, due_date=None, custom_sales_invoice_id=None, items=None):
    """Receive SI payload from HO and create a draft Purchase Invoice in Franchise."""
    try:
        frappe.log_error("Create Purchase Invoice Called", f"Supplier: {supplier}, SI: {custom_sales_invoice_id}")

        if not supplier:
            frappe.throw("Supplier is required")

        pupa_supplier = frappe.db.get_single_value("Franchise Settings", "default_supplier")
        frappe.log_error("Def Supplier", pupa_supplier)

        if not items:
            frappe.throw("Items are required")

        if isinstance(items, str):
            items = json.loads(items)

        pi = frappe.new_doc("Purchase Invoice")
        pi.supplier = pupa_supplier
        pi.company = company
        pi.posting_date = posting_date
        pi.due_date = due_date or posting_date
        pi.custom_sales_invoice_id = custom_sales_invoice_id
        pi.update_stock = 1

        for item in items:
            default_warehouse = frappe.db.get_value(
                "Item Default",
                {"parent": item.get("item_code"), "company": company},
                "default_warehouse"
            )

            pi.append("items", {
                "item_code": item.get("item_code"),
                "item_name": item.get("item_name"),
                "qty": item.get("qty"),
                "uom": item.get("uom"),
                "rate": item.get("rate"),
                "amount": item.get("amount"),
                "warehouse": default_warehouse
            })

        pi.flags.ignore_mandatory = True
        pi.insert(ignore_permissions=True)
        # Draft — franchise must approve before stock is accepted
        frappe.db.commit()

        frappe.log_error("Purchase Invoice Created", pi.name)

        return {"message": pi.name}

    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Create Purchase Invoice Error"
        )
        frappe.throw(f"Error creating Purchase Invoice: {str(e)}")


@frappe.whitelist()
def approve_purchase_invoice(purchase_invoice_name=None):
    """Franchise approves the draft Purchase Invoice — stock is officially accepted."""
    try:
        if not purchase_invoice_name:
            frappe.throw("Purchase Invoice name is required")

        pi = frappe.get_doc("Purchase Invoice", purchase_invoice_name)

        if pi.docstatus != 0:
            frappe.throw(f"Purchase Invoice '{purchase_invoice_name}' is not in Draft status")

        pi.flags.ignore_mandatory = True
        pi.submit()
        frappe.db.commit()

        frappe.log_error("Purchase Invoice Approved", pi.name)

        # Notify HO about the approval
        try:
            base_url, headers = get_api_settings()
            notify_url = f"{base_url}/api/method/pupa.api.franchise.notify_franchise_pi_approved"
            notify_payload = {
                "purchase_invoice_name": pi.name,
                "sales_invoice_id": pi.custom_sales_invoice_id
            }
            requests.post(url=notify_url, headers=headers, data=json.dumps(notify_payload))
        except Exception:
            frappe.log_error(
                message=frappe.get_traceback(),
                title="HO Notification Failed (non-critical)"
            )

        return {"message": f"Purchase Invoice '{pi.name}' approved and submitted. Stock accepted."}

    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Approve Purchase Invoice Error"
        )
        frappe.throw(f"Error approving Purchase Invoice: {str(e)}")