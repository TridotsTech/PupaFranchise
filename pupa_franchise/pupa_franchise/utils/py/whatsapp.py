import datetime
import json
import re
import urllib.parse
import frappe
from frappe.utils import formatdate
from erpnext.accounts.party import get_dashboard_info

# ------------------- HELPER FUNCTIONS -------------------

def get_10_digit_mobile(mobile_no):
    # Remove all non-digit characters and take last 10 digits (for Indian numbers)
    digits = re.sub(r"\D", "", str(mobile_no or ""))
    return digits[-10:] if len(digits) >= 10 else None


# ------------------- SALES INVOICE WHATSAPP -------------------

@frappe.whitelist()
def sales_invoice_whatsapp(name, doctype="Sales Invoice"):
    doc = frappe.get_doc(doctype, name)
    
    # Verify the document is submitted
    if doc.docstatus != 1:
        frappe.throw("Sales Invoice must be submitted to send WhatsApp.")
        
    # Get mobile number from contact_mobile; throw error if not set
    raw_mobile = doc.contact_mobile
    if not raw_mobile:
        frappe.throw("There is no Whatsapp Number in contact_mobile to send message.")
        
    clean_mobile = get_10_digit_mobile(raw_mobile)
    if not clean_mobile:
        frappe.throw(f"Invalid WhatsApp mobile number: {raw_mobile}")
    mobile_no = "91" + clean_mobile

    # Check if a successful WhatsApp Message already exists for this document
    existing_msg = frappe.db.exists("WhatsApp Message", {
        "reference_doctype": doctype,
        "reference_name": name,
        "status": "Success"
    })
    if existing_msg:
        frappe.msgprint("WhatsApp message is already sent successfully.", alert=True)
        return

    # Fetch total outstanding amount for the customer in the current company
    customer_outstanding_list = get_dashboard_info(party_type='Customer', party=doc.customer)
    outstanding_for_company = next(
        (row for row in customer_outstanding_list if row.get('company') == doc.company),
        None
    )
    total_unpaid = outstanding_for_company['total_unpaid'] if outstanding_for_company else 0.0

    # Load Franchise Settings to get configured template and print format
    pupa_settings = frappe.get_single("Franchise Settings")
    
    if not pupa_settings.sales_invoice_print_format:
        frappe.throw("Please configure <b>Sales Invoice Print Format</b> in Franchise Settings.")
        
    if not pupa_settings.sales_invoice_whatsapp_template:
        frappe.throw("Please configure <b>Sales Invoice WhatsApp Template</b> in Franchise Settings.")

    print_format = pupa_settings.sales_invoice_print_format
    template_name = pupa_settings.sales_invoice_whatsapp_template

    # Build PDF attachment URL using request host/ngrok url if available
    key = doc.get_document_share_key()
    
    # Build the URL manually with proper URL encoding to avoid spaces in query params
    base_url = frappe.utils.get_url()
    if hasattr(frappe, "request") and frappe.request:
        base_url = frappe.request.url_root.rstrip("/")

    # Force HTTPS — Meta requires it, and ngrok always exposes HTTPS even if internally HTTP
    base_url = base_url.replace("http://", "https://")

    query_params = urllib.parse.urlencode({
        "doctype": doctype,
        "name": name,
        "format": print_format,
        "no_letterhead": 0,
        "key": key
    })
    url = f"{base_url}/api/method/frappe.utils.print_format.download_pdf?{query_params}"

    # Define template parameters explicitly in body_param mapping to template placeholder names
    body_param_dict = {
        "customer_name": doc.customer_name
    }

    # Ensure the WhatsApp Template in the DB has sample_values set so that the parameters are processed
    template = frappe.get_doc("WhatsApp Templates", template_name)
    if not template.sample_values:
        template.db_set("sample_values", "customer_name")

    # Create WhatsApp Message using the template
    wa_message = frappe.get_doc({
        "doctype": "WhatsApp Message",
        "to": mobile_no,
        "type": "Outgoing",
        "message_type": "Template",
        "reference_doctype": doctype,
        "reference_name": name,
        "label": name,
        "content_type": "document",
        "use_template": 1,
        "template": template_name,
        "attach": url,
        "body_param": json.dumps(body_param_dict)
    })
    try:
        # This will trigger before_insert -> send_outgoing -> send_template -> notify
        wa_message.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        latest_logs = frappe.get_all("WhatsApp Notification Log", order_by="creation desc", limit=5, fields=["template", "meta_data"])
        frappe.log_error(title="WhatsApp Step 6: Failure during insert/send", message=f"Error: {str(e)}\nLogs: {json.dumps(latest_logs)}")
        frappe.throw(f"Failed to send template. Error: {str(e)}")
    
    frappe.msgprint("WhatsApp message queued successfully.")
