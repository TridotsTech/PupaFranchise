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


def generate_whatsapp_api_url(log, pupa_settings):
    url = pupa_settings.whatsapp_url
    token = pupa_settings.token
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
    pupa_settings = frappe.get_single("Franchise Settings")
    whatsapp_no = frappe.get_value("Customer", doc.customer, "mobile_no")
    if not pupa_settings.enable_whatsapp:
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

    print_format = pupa_settings.sales_invoice_print_format
    custom_message_template = pupa_settings.sales_message
    return_message_template = pupa_settings.sales_invoice_return
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
    api_url = generate_whatsapp_api_url(dummy_log, pupa_settings)

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

# ------------------- PAYMENT ENTRY WHATSAPP -------------------

@frappe.whitelist()
def payment_entry_whatsapp(name, doctype="Payment Entry"):
    doc = frappe.get_doc(doctype, name)
    pupa_settings = frappe.get_single("Franchise Settings")
    mobile_no = frappe.get_value(doc.party_type, doc.party, 'mobile_no')
    whatsapp_no = get_10_digit_mobile(mobile_no)

    if not pupa_settings.enable_whatsapp:
        return

    existing_log = frappe.db.exists("Whatsapp Log", {
        "reference_doctype": doctype,
        "reference_docname": name,
        "status": ["in", ["Queue", "Success"]]
    })
    if not whatsapp_no:
        frappe.msgprint("There is no WhatsApp number in party master.")
        return
    if existing_log:
        frappe.msgprint("WhatsApp message is already sent.", alert=True)
        return

    custom_message_template = (
        pupa_settings.payment_receive if doc.payment_type == "Receive"
        else pupa_settings.payment_paid
    )

    formatted_date = formatdate(doc.posting_date, "dd-mm-yyyy")

    if doc.party_type == 'Customer':
        customer_outstanding_list = get_dashboard_info(party_type='Customer', party=doc.party)

        # Filter to get outstanding specific to the Payment Entry's company
        outstanding_for_company = next(
            (row for row in customer_outstanding_list if row.get('company') == doc.company),
            None
        )
        total_outstanding = outstanding_for_company['total_unpaid'] if outstanding_for_company else 0.0

    elif doc.party_type == 'Supplier':
        supplier_name = doc.party
        total_outstanding = get_supplier_outstanding(supplier_name, doc.company)

    else:
        total_outstanding = 0.0  # default fallback

    message = custom_message_template.format(
        doc.party, formatted_date, doc.name, doc.paid_amount, total_outstanding
    )

    dummy_log = frappe._dict({
        "mobile_number": whatsapp_no,
        "message": message,
        "file_url": None,
    })
    api_url = generate_whatsapp_api_url(dummy_log, pupa_settings)

    log_whatsapp_activity(
        reference_doctype=doctype,
        reference_name=doc.name,
        party=doc.party,
        status="Queue",
        message=message,
        media_url=None,
        api_url=api_url,
        mobile_number=whatsapp_no
    )
    frappe.msgprint("WhatsApp message queued successfully.")

# ------------------- DAILY REPORT WHATSAPP -------------------

@frappe.whitelist()
def send_daily_report_whatsapp_messages():
    date = nowdate()
    today = formatdate(date, "dd-mm-yyyy")

    # Fetch data
    sales_invoices = frappe.db.get_all("Sales Invoice", {
        "company": "PUPA CERAMIC", "posting_date": date, "docstatus": 1
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

    pupa_settings = frappe.get_single("Franchise Settings")
    if not pupa_settings.enable_whatsapp:
        return

    template = pupa_settings.daily_report_message or ""
    message = template.format(today, invoice_count, total_sales, total_payment_received, total_payment_paid)

    for row in pupa_settings.report_message_to:
        mobile_no = get_10_digit_mobile(row.mobile_no)
        if not mobile_no:
            continue

        dummy_log = frappe._dict({
            "mobile_number": mobile_no,
            "message": message,
            "file_url": None,
        })
        api_url = generate_whatsapp_api_url(dummy_log, pupa_settings)

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
    frappe.msgprint("Daily WhatsApp report queued for all recipients.")

# ------------------- SALES PERSON REPORT WHATSAPP -------------------

try:
    from pupa_franchise.pupa_franchise.report.sales_person_outstanding.sales_person_outstanding import execute as execute_sales_person_outstanding
except ImportError:
    execute_sales_person_outstanding = None

@frappe.whitelist()
def send_sales_person_reports():
    company = "PUPA CERAMIC"
    pupa_settings = frappe.get_single("Franchise Settings")
    if not pupa_settings.enable_whatsapp or not pupa_settings.send_sales_person_report:
        return

    if not execute_sales_person_outstanding:
        frappe.throw("Sales Person Outstanding Report is not installed.")

    # Fetch distinct sales persons
    sales_persons = frappe.db.sql("""
        SELECT DISTINCT custom_sales_person AS sales_person
        FROM `tabCustomer`
        WHERE custom_sales_person IS NOT NULL AND custom_sales_person != ''
    """, as_dict=1)

    for sp in sales_persons:
        sales_person = sp.sales_person
        if not sales_person:
            continue

        # Get Employee linked to this Sales Person
        employee = frappe.db.get_value("Sales Person", sales_person, "employee")
        if not employee:
            continue

        # Get Employee's mobile number
        mobile_no = frappe.db.get_value("Employee", employee, "cell_number")
        mobile_no = get_10_digit_mobile(mobile_no)
        if not mobile_no:
            continue

        # Only now: generate report & PDF
        filters = {
            "company": company,
            "sales_person": sales_person,
            "is_group_by_sales_person": 0
        }
        logo_path = frappe.db.get_value("Company", company, "logo_for_printing")
        full_logo_url = f"{get_url()}{logo_path}" if logo_path else ""

        report_data = execute_sales_person_outstanding(filters)
        if not report_data[1]:
            continue  # Skip if no data to report

        report_data_html = frappe.render_template(
            "pupa_franchise/templates/sales_person_outstanding.html",
            {
                "filters": filters,
                "data": report_data[1],
                "logo": full_logo_url,
            },
        )

        pdf_content = get_pdf(report_data_html, {"orientation": "Portrait"})
        safe_name = re.sub(r'[^\w\s-]', '_', sales_person).strip().replace(" ", "_")

        file_doc = frappe.new_doc("File")
        file_doc.file_name = f"{safe_name}_outstanding_report.pdf"
        file_doc.content = pdf_content
        file_doc.attached_to_doctype = "Sales Person"
        file_doc.attached_to_name = sales_person
        file_doc.file_type = "PDF"
        file_doc.custom_for_whatsapp = 1
        file_doc.save(ignore_permissions=True)

        frappe.db.commit()

        domain_url = get_url()
        full_file_url = f"{domain_url}{file_doc.file_url}"
        dummy_log = frappe._dict({
            "mobile_number": mobile_no,
            "message": "Sales Person Outstanding Report",
            "file_url": full_file_url,
        })
        api_url = generate_whatsapp_api_url(dummy_log, pupa_settings)

        log_whatsapp_activity(
            reference_doctype=None,
            reference_name=None,
            party=sales_person,
            status="Queue",
            message="Sales Person Outstanding Report",
            media_url=full_file_url,
            api_url=api_url,
            mobile_number=mobile_no,
        )

    frappe.msgprint("Sales Person outstanding WhatsApp reports queued.")

# ------------------- DELETE WHATSAPP PDF FILES (Optional) -------------------

@frappe.whitelist()
def delete_whatsapp_pdf_files():
    files = frappe.get_all("File", filters={"custom_for_whatsapp": 1}, pluck="name")
    for file_name in files:
        frappe.delete_doc("File", file_name, ignore_permissions=True)

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
        except Exception as e:
            frappe.db.set_value("Whatsapp Log", log.name, "status", "Failure")
            frappe.log_error(f"Error sending WhatsApp message: {e}", "WhatsApp Message Sending Error")

# ----------------------------------------------------------

def get_supplier_outstanding(supplier_name, company):
    balance = frappe.db.sql("""
        SELECT SUM(debit - credit) AS balance
        FROM `tabGL Entry`
        WHERE party_type='Supplier' AND party=%s AND company=%s AND is_cancelled=0
    """, (supplier_name, company), as_dict=True)
    return balance[0]['balance'] or 0.0
