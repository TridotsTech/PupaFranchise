import datetime
import json
import re
import requests
import urllib.parse
import frappe
from frappe.utils import nowdate, formatdate
from frappe.utils.data import get_url
from frappe.utils.pdf import get_pdf
from erpnext.accounts.party import get_dashboard_info

# ------------------- HELPER FUNCTIONS -------------------

def get_10_digit_mobile(mobile_no):
    # Remove all non-digit characters and take last 10 digits (for Indian numbers)
    digits = re.sub(r"\D", "", str(mobile_no or ""))
    return digits[-10:] if len(digits) >= 10 else None


def generate_whatsapp_api_url(log, settings):
    url = settings.whatsapp_url
    token = settings.whatsapp_token
    base_phone = "91" + str(log.mobile_number)
    if log.file_url:
        return (
            f"{url}sendFileWithCaption?"
            f"phone={base_phone}&"
            f"link={urllib.parse.quote_plus(log.file_url)}&"
            f"message={urllib.parse.quote(log.message)}&"
            f"token={token}"
        )
    else:
        return (
            f"{url}sendText?"
            f"phone={base_phone}&"
            f"message={urllib.parse.quote(log.message)}&"
            f"token={token}"
        )

def log_whatsapp_activity(
    reference_doctype, message, media_url, reference_name, party, status, mobile_number, api_url=None
):
    frappe.get_doc({
        "doctype": "Whatsapp Log",
        "reference_doctype": reference_doctype,
        "reference_docname": reference_name,
        "party": party,
        "status": status,
        "message": message,
        "file_url": media_url,
        "api_url": api_url,
        "mobile_number": mobile_number,
        "date": datetime.datetime.now()
    }).insert(ignore_permissions=True)


# ------------------- SALES INVOICE WHATSAPP -------------------

@frappe.whitelist()
def sales_invoice_whatsapp(name, doctype="Sales Invoice"):
    doc = frappe.get_doc(doctype, name)
    settings = frappe.get_single("Franchise Settings")
    whatsapp_no = frappe.get_value("Customer", doc.customer, "mobile_no")
    
    if not settings.enable_whatsapp:
        return

    existing_log = frappe.db.exists("Whatsapp Log", {
        "reference_doctype": doctype,
        "reference_docname": name,
        "status": ["in", ["Queue", "Success"]]
    })
    
    if not whatsapp_no:
        frappe.msgprint("There is no Whatsapp Number in customer to send message.")
        return
        
    if existing_log:
        frappe.msgprint("WhatsApp message is already sent.", alert=True)
        return

    customer_outstanding_list = get_dashboard_info(party_type='Customer', party=doc.customer)

    # Filter to get outstanding specific to the invoice's company
    outstanding_for_company = next(
        (row for row in customer_outstanding_list if row.get('company') == doc.company),
        None
    )
    total_unpaid = outstanding_for_company['total_unpaid'] if outstanding_for_company else 0.0

    print_format = settings.sales_invoice_print_format
    custom_message_template = settings.sales_message
    return_message_template = settings.sales_invoice_return
    formatted_date = formatdate(doc.posting_date, "dd-mm-yyyy")

    if doc.is_return:
        message = return_message_template.format(
            doc.customer_name,
            formatted_date,
            doc.name,
            doc.grand_total,
            total_unpaid
        )
    else:
        message = custom_message_template.format(
            doc.customer_name,
            formatted_date,
            doc.name,
            doc.grand_total,
            total_unpaid
        )

    fcontent = frappe.get_print(doc=doc, as_pdf=1, no_letterhead=1, print_format=print_format)
    pdf_file_name = f"{doc.name}.pdf"

    _file = frappe.get_doc({
        "doctype": "File",
        "file_name": pdf_file_name,
        "content": fcontent,
        "custom_for_whatsapp": 1
    })
    _file.insert(ignore_permissions=True)

    file_url = frappe.utils.get_url() + _file.file_url
    
    dummy_log = frappe._dict({
        "mobile_number": get_10_digit_mobile(whatsapp_no),
        "message": message,
        "file_url": file_url,
    })
    api_url = generate_whatsapp_api_url(dummy_log, settings)

    log_whatsapp_activity(
        reference_doctype=doctype,
        reference_name=doc.name,
        party=doc.customer_name,
        status="Queue",
        message=message,
        media_url=file_url,
        api_url=api_url,
        mobile_number=get_10_digit_mobile(whatsapp_no),
    )
    frappe.msgprint("WhatsApp message queued successfully.")


# ------------------- DAILY REPORT WHATSAPP -------------------

@frappe.whitelist()
def send_daily_report_whatsapp_messages():
    date = nowdate()
    today = formatdate(date, "dd-mm-yyyy")

    settings = frappe.get_single("Franchise Settings")
    if not settings.enable_whatsapp:
        return

    # Fetch data (Example for Franchise)
    sales_invoices = frappe.db.get_all("Sales Invoice", {
        "posting_date": date, "docstatus": 1
    }, ["name", "grand_total"])

    invoice_count = len(sales_invoices)
    total_sales = round(sum(inv.grand_total for inv in sales_invoices), 2)

    payments_received = frappe.db.get_all("Payment Entry", {
        "posting_date": date, "payment_type": "Receive", "docstatus": 1
    }, ["paid_amount"])
    total_payment_received = round(sum(p.paid_amount for p in payments_received), 2)

    payments_paid = frappe.db.get_all("Payment Entry", {
        "posting_date": date, "payment_type": "Pay", "docstatus": 1
    }, ["paid_amount"])
    total_payment_paid = round(sum(p.paid_amount for p in payments_paid), 2)

    template = settings.daily_report_message or ""
    try:
        message = template.format(today, invoice_count, total_sales, total_payment_received, total_payment_paid)
    except Exception:
        message = template

    for row in settings.report_message_to:
        mobile_no = get_10_digit_mobile(row.mobile_no)
        if not mobile_no:
            continue

        dummy_log = frappe._dict({
            "mobile_number": mobile_no,
            "message": message,
            "file_url": None,
        })
        api_url = generate_whatsapp_api_url(dummy_log, settings)

        log_whatsapp_activity(
            reference_doctype=None,
            reference_name=None,
            party=mobile_no,
            status="Queue",
            message=message,
            media_url=None,
            api_url=api_url,
            mobile_number=mobile_no,
        )

# ------------------- TRIGGER FUNCTION TO SEND ALL QUEUED WHATSAPP MESSAGES -------------------

@frappe.whitelist()
def send_queued_whatsapp_logs():
    logs = frappe.get_all("Whatsapp Log", filters={"status": "Queue"}, fields=["name", "api_url", "reference_doctype", "reference_docname"])
    for log in logs:
        try:
            if not log.api_url:
                continue
            response = requests.post(log.api_url)
            response_json = response.json()
            if response_json.get("status", "").lower() == "success":
                frappe.db.set_value("Whatsapp Log", log.name, "status", "Success")
                if log.reference_doctype and log.reference_docname:
                    try:
                        frappe.db.set_value(log.reference_doctype, log.reference_docname, "custom_message_status", "Sent")
                    except Exception:
                        pass
            else:
                frappe.db.set_value("Whatsapp Log", log.name, "status", "Failure")
                frappe.log_error(f"WhatsApp API returned failure: {response_json}", "WhatsApp API Failure")
        except Exception as e:
            frappe.db.set_value("Whatsapp Log", log.name, "status", "Failure")
            frappe.log_error(f"Error sending WhatsApp message: {e}", "WhatsApp Message Sending Error")

@frappe.whitelist()
def delete_whatsapp_pdf_files():
    files = frappe.get_all("File", filters={"custom_for_whatsapp": 1}, pluck="name")
    for file_name in files:
        frappe.delete_doc("File", file_name, ignore_permissions=True)
