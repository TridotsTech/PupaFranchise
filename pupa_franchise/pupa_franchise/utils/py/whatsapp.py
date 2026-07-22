import datetime
import json
import re
import urllib.parse
import frappe
from frappe.utils import formatdate
from erpnext.accounts.party import get_dashboard_info
from frappe import _

# ------------------- HELPER FUNCTIONS -------------------

def get_formatted_whatsapp_mobile(mobile_no):
    if not mobile_no:
        return None
    # Strip spaces, dashes, parentheses and '+'
    cleaned = re.sub(r"[\s\-\(\)\+]", "", str(mobile_no))
    
    # If it starts with 91 and has 12 digits, keep it as is
    if cleaned.startswith("91") and len(cleaned) == 12:
        return cleaned
        
    # If it is a 10-digit number, prepend 91
    if len(cleaned) == 10:
        return "91" + cleaned

    return None


# ------------------- SALES INVOICE WHATSAPP -------------------

@frappe.whitelist()
def sales_invoice_whatsapp(name, doctype="Sales Invoice"):
    doc = frappe.get_doc(doctype, name)
    frappe.log_error("DOCTYPE", doc)

    if doc.docstatus !=1:
        frappe.throw(_("Sales Invoice must be submitted to send WhatsApp Message"))

    raw_mobile = doc.contact_mobile
    frappe.log_error("WHATSAPP No:", raw_mobile)

    if not raw_mobile:
        frappe.throw(_("Customer WhatsApp number not defined.!"))

    mobile_no = get_formatted_whatsapp_mobile(raw_mobile)
    frappe.log_error("FORMATTED NO:", mobile_no)

    if not mobile_no:
        frappe.throw(_(f"Invalid WhatsApp Number: {raw_mobile}"))

    whatsapp_settings = frappe.get_single("Franchise Settings")

    if not whatsapp_settings.sales_invoice_print_format:
        frappe.throw(_("Please configure <b>Sales Invoice Print Format</b> in Franchise Settings."))

    if not whatsapp_settings.sales_invoice_whatsapp_template:
        frappe.throw(_("Please configure <b>Sales Invoice WhatsApp Template</b> in Franchise Settings."))

    print_format = whatsapp_settings.sales_invoice_print_format
    template_name = whatsapp_settings.sales_invoice_whatsapp_template

    key = doc.get_document_share_key()
    frappe.log_error("KEY", key)

    base_url = frappe.utils.get_url()
    frappe.log_error("BASE URL", base_url)

    if hasattr(frappe, "request") and frappe.request:
        base_url = frappe.request.url_root.rstrip("/")

    base_url = base_url.replace("http://", "https://")

    query_params = urllib.parse.urlencode({
        "doctype": doctype,
        "name": name,
        "format": print_format,
        "no_letterhead": 0,
        "key": key
    })

    frappe.log_error("QUERY PARAMS", query_params)

    url = f"{base_url}/api/method/frappe.utils.print_format.download_pdf?{query_params}"

    frappe.log_error("PDF URL", url)

    body_parms_dict = {
        "customer_name": doc.customer_name
    }

    template = frappe.get_doc("WhatsApp Templates", template_name)
    if not template.sample_values:
        template.db_set("sample_values", "customer_name")

    whatsapp_message = frappe.get_doc({
        "doctype": "WhatsApp Message",
        "label": name,
        "to": mobile_no,
        "type": "Outgoing",
        "reference_doctype": doctype,
        "reference_name": name,
        "content_type": "document",
        "use_template": 1,
        "template": template_name,
        "attach": url,
        "body_param": json.dumps(body_parms_dict)
    })

    frappe.log_error("WHATSAPP MSG", whatsapp_message)

    try:
        whatsapp_message.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(title="WhatsApp Send Failrue", message=f"Error: {str(e)}")
        frappe.throw(f"Failed to send template. Error: {str(e)}")

    frappe.msgprint(_("WhatsApp message queued successfully!"))

