from requests import request
import frappe
import json
import requests

# api function
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

    if item_group and not frappe.db.exists("Item Group", item_group):
        frappe.log_error("Franchise Item Sync Skipped", f"Item Group '{item_group}' does not exist in franchise")
        return {"status": "skipped", "reason": f"Item Group '{item_group}' not found"}

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

    return {"status": "skipped", "reason": "Item already exists"}

@frappe.whitelist()
def create_item_group(item_group_name=None, parent_item_group=None, is_group=None, franchise_group=None):
    frappe.log_error("Func Called IG")

    if not item_group_name:
        frappe.throw("Item Group is Required!")

    if not franchise_group or int(franchise_group) != 1:
        return {"status": "skipped", "reason": "Not a franchise item group"}

    if not frappe.db.exists("Item Group", item_group_name):
        item_grp = frappe.new_doc("Item Group")
        item_grp.item_group_name = item_group_name
        item_grp.parent_item_group = parent_item_group
        item_grp.is_group = is_group

        item_grp.insert(ignore_permissions=True)
        frappe.db.commit()

        return item_grp.name

    return {"status": "skipped", "reason": "Item Group already exists"}

# @frappe.whitelist()
# def create_supplier(supplier_name=None, supplier_type=None):
#     frappe.log_error("Supplier Func Called")
#     if not supplier_name or not supplier_type:
#         return 

#     if not frappe.db.exists("Supplier", supplier_name):
#         supplier = frappe.new_doc("Supplier")
#         supplier.supplier_name = supplier_name
#         supplier.supplier_type = supplier_type

#         supplier.insert(ignore_permissions=True)
#         frappe.db.commit()

#         return supplier.name


@frappe.whitelist()
def create_branch(branch_name=None):
    frappe.log_error("branch Func called")
    if not branch_name:
        return

    if not frappe.db.exists("Branch", branch_name):
        branch = frappe.new_doc("Branch")
        branch.branch = branch_name

        branch.insert(ignore_permissions=True)
        frappe.db.commit()

        return branch.name
    


@frappe.whitelist()
def create_company(company_name=None, branch_name=None):
    frappe.log_error("Company Func Called")
    if not company_name or not branch_name:
        return

    settings = frappe.get_single("System Settings")
    default_currency = settings.currency
    country = settings.country

    if not frappe.db.exists("Company", company_name):
        company = frappe.new_doc("Company")
        company.company_name = company_name
        company.default_currency = default_currency
        company.country = country
        company.custom_branch = branch_name
        company.gst_category = "Unregistered"

        company.insert(ignore_permissions=True)
        company.flags.ignore_mandatory = True

        frappe.db.commit()

        return company.name

# This commented method not reqd as of now.

# @frappe.whitelist()
# def get_stock_from_pupa(branch):
#     try:
#         base_url, headers = get_api_settings()
#         get_url = f"{base_url}/api/method/pupa.api.franchise.get_branch_stock"

#         response = requests.get(
#             url = get_url,
#             headers = headers,
#             params = {"branch_name": branch}
#         )

#         if response.status_code != 200:
#             frappe.throw("Error connecting to Pupa")

#         return response.json().get("message", [])

#     except Exception as e:
#         frappe.log_error(
#             message=frappe.get_traceback(),
#             title="Pupa Branch Stock Error"
#         )


@frappe.whitelist()
def get_warehouse_available_stock(warehouse):
    if not warehouse:
        return []

    stock = frappe.db.sql("""
    SELECT
        item_code,
        actual_qty
    FROM 
        `tabBin`
    WHERE
        warehouse = %s
    AND actual_qty > 0
    """, (warehouse,), as_dict=True)

    return stock


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
            "customer": doc.company,
            "company": settings.hq_company,
            "transaction_date": str(doc.transaction_date),
            "delivery_date": str(doc.schedule_date) if doc.schedule_date else str(doc.transaction_date),
            "custom_franchise_po_id": doc.name,
            "branch": doc.custom_branch,
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
def create_purchase_invoice(company=None, posting_date=None, due_date=None, 
    custom_sales_invoice_id=None, custom_franchise_po_id=None, 
    items=None):

    """Receive SI payload from HO and create a draft Purchase Invoice in Franchise."""
    try:
        supplier_data = None
        if custom_franchise_po_id:
            supplier_data = frappe.db.get_value("Purchase Order", {"name": custom_franchise_po_id}, "supplier")
        
        if not supplier_data:
            supplier_data = frappe.db.get_single_value("Franchise Settings", "default_supplier")
        
        frappe.log_error("Supplier Name for PI", supplier_data)

        if not supplier_data:
            frappe.throw("Supplier could not be determined. Please set a Default Supplier in Franchise Settings or ensure the Purchase Order exists.")

        if not items:
            frappe.throw("Items are required")

        if isinstance(items, str):
            items = json.loads(items)

        pi = frappe.new_doc("Purchase Invoice")
        pi.supplier = supplier_data
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



import frappe
import json


@frappe.whitelist(allow_guest=True)
def create_or_update_pricing_rule(**kwargs):
    """Receive a Pricing Rule from HO and create or update it in the Franchise instance."""
    try:
        ho_pricing_rule_id = kwargs.get("custom_ho_pricing_rule_id")
        if not ho_pricing_rule_id:
            frappe.throw("ho_pricing_rule_id is required")

        # Parse child table data if passed as strings
        items = kwargs.get("items") or []
        item_groups = kwargs.get("item_groups") or []
        brands = kwargs.get("brands") or []

        if isinstance(items, str):
            items = json.loads(items)
        if isinstance(item_groups, str):
            item_groups = json.loads(item_groups)
        if isinstance(brands, str):
            brands = json.loads(brands)

        # Check if a Pricing Rule with this HO ID already exists
        existing = frappe.db.get_value(
            "Pricing Rule",
            {"custom_ho_pricing_rule_id": ho_pricing_rule_id},
            "name"
        )

        franchise_company = frappe.db.get_single_value("Franchise Settings", "default_franchise_company")

        if existing:
            pr = frappe.get_doc("Pricing Rule", existing)
        else:
            pr = frappe.new_doc("Pricing Rule")
            pr.custom_ho_pricing_rule_id = ho_pricing_rule_id

        # Set all fields from the payload
        pr.title = kwargs.get("title")
        pr.apply_on = kwargs.get("apply_on", "Item Code")
        pr.price_or_product_discount = kwargs.get("price_or_product_discount", "Price")
        pr.selling = int(kwargs.get("selling", 0))
        pr.buying = int(kwargs.get("buying", 0))
        pr.applicable_for = kwargs.get("applicable_for") or ""
        pr.customer = kwargs.get("customer") or ""
        pr.customer_group = kwargs.get("customer_group") or ""
        pr.territory = kwargs.get("territory") or ""
        pr.sales_partner = kwargs.get("sales_partner") or ""
        pr.campaign = kwargs.get("campaign") or ""
        pr.supplier = kwargs.get("supplier") or ""
        pr.supplier_group = kwargs.get("supplier_group") or ""
        pr.min_qty = float(kwargs.get("min_qty", 0))
        pr.max_qty = float(kwargs.get("max_qty", 0))
        pr.min_amt = float(kwargs.get("min_amt", 0))
        pr.max_amt = float(kwargs.get("max_amt", 0))
        pr.valid_from = kwargs.get("valid_from") or None
        pr.valid_upto = kwargs.get("valid_upto") or None
        pr.company = franchise_company
        pr.currency = kwargs.get("currency") or "INR"
        pr.rate_or_discount = kwargs.get("rate_or_discount") or ""
        pr.rate = float(kwargs.get("rate", 0))
        pr.discount_percentage = float(kwargs.get("discount_percentage", 0))
        pr.discount_amount = float(kwargs.get("discount_amount", 0))
        pr.for_price_list = kwargs.get("for_price_list") or ""
        pr.margin_type = kwargs.get("margin_type") or ""
        pr.margin_rate_or_amount = float(kwargs.get("margin_rate_or_amount", 0))
        pr.apply_discount_on = kwargs.get("apply_discount_on") or ""
        pr.warehouse = kwargs.get("warehouse") or ""
        pr.condition = kwargs.get("condition") or ""
        pr.disable = int(kwargs.get("disable", 0))
        pr.mixed_conditions = int(kwargs.get("mixed_conditions", 0))
        pr.is_cumulative = int(kwargs.get("is_cumulative", 0))
        pr.apply_multiple_pricing_rules = int(kwargs.get("apply_multiple_pricing_rules", 0))
        pr.apply_discount_on_rate = int(kwargs.get("apply_discount_on_rate", 0))
        pr.has_priority = int(kwargs.get("has_priority", 0))
        pr.priority = kwargs.get("priority") or ""
        pr.apply_rule_on_other = kwargs.get("apply_rule_on_other") or ""
        pr.other_item_code = kwargs.get("other_item_code") or ""
        pr.other_item_group = kwargs.get("other_item_group") or ""
        pr.other_brand = kwargs.get("other_brand") or ""
        pr.same_item = int(kwargs.get("same_item", 0))
        pr.free_item = kwargs.get("free_item") or ""
        pr.free_qty = float(kwargs.get("free_qty", 0))
        pr.free_item_uom = kwargs.get("free_item_uom") or ""
        pr.free_item_rate = float(kwargs.get("free_item_rate", 0))
        pr.is_recursive = int(kwargs.get("is_recursive", 0))
        pr.recurse_for = float(kwargs.get("recurse_for", 0))
        pr.apply_recursion_over = float(kwargs.get("apply_recursion_over", 0))

        # Clear and re-add child tables
        pr.items = []
        for item in items:
            pr.append("items", {
                "item_code": item.get("item_code"),
                "uom": item.get("uom")
            })

        pr.item_groups = []
        for ig in item_groups:
            pr.append("item_groups", {
                "item_group": ig.get("item_group"),
                "uom": ig.get("uom")
            })

        pr.brands = []
        for b in brands:
            pr.append("brands", {
                "brand": b.get("brand")
            })

        pr.flags.ignore_permissions = True
        pr.flags.ignore_mandatory = True
        pr.save()
        frappe.db.commit()

        action = "updated" if existing else "created"
        frappe.log_error(
            f"Pricing Rule {action}: {pr.name} (HO ID: {ho_pricing_rule_id})",
            "Franchise Pricing Rule Sync"
        )

        # If this was an update, recalculate draft POs/SOs using this pricing rule
        if existing:
            update_draft_transactions_for_pricing_rule(pr.name)

        return {"message": f"Pricing Rule {action} successfully", "name": pr.name}

    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Franchise Pricing Rule Sync Error"
        )
        frappe.throw(f"Error creating/updating Pricing Rule: {str(e)}")


def update_draft_transactions_for_pricing_rule(pricing_rule_name):
    """Enqueue a background job to update draft Purchase Orders
    when a Pricing Rule with buying=1 is changed."""
    try:
        pr = frappe.get_doc("Pricing Rule", pricing_rule_name)

        if not pr.buying:
            return

        item_codes = [row.item_code for row in (pr.get("items") or []) if row.item_code]
        if not item_codes:
            return

        # Check if any draft POs exist with these items before enqueuing
        po_exists = frappe.db.sql("""
            SELECT 1 FROM `tabPurchase Order Item`
            WHERE item_code IN %s AND docstatus = 0
            LIMIT 1
        """, (item_codes,))

        if not po_exists:
            return

        frappe.enqueue(
            "pupa_franchise.api.api_sync._update_draft_pos_for_pricing_rule",
            queue="long",
            pricing_rule_name=pricing_rule_name,
            now=frappe.flags.in_test
        )

    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Draft PO Update Enqueue Error"
        )


def _update_draft_pos_for_pricing_rule(pricing_rule_name):
    """Background job: update rates in all draft Purchase Orders
    affected by the given Pricing Rule (only when buying=1)."""
    try:
        pr = frappe.get_doc("Pricing Rule", pricing_rule_name)

        if not pr.buying:
            return

        item_codes = [row.item_code for row in (pr.get("items") or []) if row.item_code]
        if not item_codes:
            return

        # Find all draft POs containing these items
        po_items = frappe.db.sql("""
            SELECT DISTINCT parent
            FROM `tabPurchase Order Item`
            WHERE item_code IN %s
            AND docstatus = 0
        """, (item_codes,), as_dict=True)

        if not po_items:
            return

        po_names = list(set([d.parent for d in po_items]))

        for po_name in po_names:
            try:
                po = frappe.get_doc("Purchase Order", po_name)
                updated = False

                for item in po.items:
                    if item.item_code in item_codes:
                        base_rate = item.price_list_rate or item.custom_mrp or 0
                        new_rate = None

                        if pr.rate_or_discount == "Discount Percentage" and pr.discount_percentage:
                            new_rate = base_rate * (1 - pr.discount_percentage / 100)
                        elif pr.rate_or_discount == "Discount Amount" and pr.discount_amount:
                            new_rate = base_rate - pr.discount_amount
                        elif pr.rate_or_discount == "Rate" and pr.rate:
                            new_rate = pr.rate

                        if new_rate is not None:
                            item.rate = new_rate
                            updated = True

                if updated:
                    po.calculate_taxes_and_totals()
                    po.flags.ignore_permissions = True
                    po.flags.ignore_mandatory = True
                    po.save()
                    frappe.db.commit()
                    frappe.log_error(
                        f"Updated draft PO '{po_name}' rates from Pricing Rule '{pr.name}'",
                        "Pricing Rule PO Update"
                    )

            except Exception:
                frappe.log_error(
                    message=frappe.get_traceback(),
                    title=f"Error updating PO {po_name} from Pricing Rule"
                ) 

    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Pricing Rule Draft PO Update Error"
        )


@frappe.whitelist()
def get_pupa_warehouses():
    """Fetch the franchise allowed warehouses from Pupa (HQ) instance."""
    try:
        base_url, headers = get_api_settings()

        response = requests.get(
            url=f"{base_url}/api/method/pupa.api.franchise.get_franchise_allowed_warehouses",
            headers=headers
        )

        if response.status_code != 200:
            frappe.log_error(
                message=f"Status: {response.status_code}\nResponse: {response.text}",
                title="Pupa Warehouse Fetch Error"
            )
            return []

        return response.json().get("message", [])

    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Pupa Warehouse Fetch Error"
        )
        return []
