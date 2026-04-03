import frappe
from frappe.utils import flt, today
import frappe
from frappe import _

def on_submit(doc, method):
    create_pi_for_influencer_si(doc.name)

# by MK
@frappe.whitelist()
def get_sales_person_mobile(sales_person):
    """
    Fetches mobile number from employee linked to sales person
    """
    if not sales_person:
        return {'status': 'error', 'message': _('Sales Person not provided')}
    
    sales_person_doc = frappe.get_doc('Sales Person', sales_person)
    
    if not sales_person_doc.employee:
        return {
            'status': 'error',
            'message': _('Please set Employee for Sales Person: {0}').format(sales_person),
            'title': _('Employee Not Linked')
        }
    
    employee_doc = frappe.get_doc('Employee', sales_person_doc.employee)
    
    if not employee_doc.cell_number:
        return {
            'status': 'error',
            'message': _('Please set Mobile Number for Employee: {0}').format(sales_person_doc.employee),
            'title': _('Mobile Number Not Found')
        }
    
    return {
        'status': 'success',
        'mobile_number': employee_doc.cell_number,
        'employee': sales_person_doc.employee
    }

# SI -> PI creation
@frappe.whitelist()
def create_pi_for_influencer_si(si_name):
    si = frappe.get_doc("Sales Invoice", si_name)

    if not si.custom_do_you_have_any_influencer:
        return

    influencer_rows = si.get("custom_influencer_commission_details")

    if not influencer_rows:
        frappe.msgprint("No Nnfluencer Commission Details Found")
        return

    created_invoices = []

    for row in influencer_rows:
        if not row.supplier or not row.commission_percentage:
            continue

        supplier_name = row.supplier
        commission_prct = flt(row.commission_percentage)
        grand_total = flt(si.grand_total)
        commission_amount = (grand_total * commission_prct) / 100

        pi_items = []
        for item in si.items:
            item_rate = flt(item.rate)
            commission_rate = (item_rate * commission_prct) / 100

            pi_items.append({
                "doctype": "Sales Invoice Item",
                "item_code": item.item_code,
                "item_name": item.item_name,
                "description": item.description or item.item_name,
                "qty": flt(item.qty),
                "uom": item.uom,
                "rate": commission_rate,
                "amount": commission_rate * flt(item.qty),
                "cost_center": frappe.db.get_value(
                    "Company", si.company, "cost_center"
                )
            })

        pi = frappe.new_doc("Purchase Invoice")
        pi.supplier = supplier_name
        pi.company = si.company
        pi.posting_date = frappe.utils.today()
        pi.due_date = frappe.utils.today()
        pi.currency = si.currency
        pi.buying_price_list = "Standard Buying"
        pi.custom_influencer_sales_invoice_reference = si_name
        pi.set("items", pi_items)
        pi.insert(ignore_permissions=True)

        created_invoices.append(pi.name)

        frappe.msgprint(
            f"Purchase Invoice <b>{pi.name}</b> created for Supplier <b>{supplier_name}</b>"
            f"with {commission_prct}% discount (Amount: {commission_amount}).",
            alert=True
        )

    return created_invoices


def get_tax_table_sales_invoice(doctype,doc):
	pos = frappe.get_cached_doc(doctype, doc)
	tax_row = {}

	for it in pos.items:
		if pos.tax_category == 'In-State':
			gst_rate = it.cgst_rate + it.sgst_rate
		else:
			gst_rate = it.igst_rate

		taxable_value = it.net_amount
		if gst_rate == 0:
			continue  # Skip if no GST applies

		if gst_rate in tax_row:
			tax_row[gst_rate]['taxable_value'] += taxable_value
			if pos.tax_category == 'In-State':
				tax_row[gst_rate]['cgst_amount'] += (it.cgst_rate / 100) * taxable_value
				tax_row[gst_rate]['sgst_amount'] += (it.sgst_rate / 100) * taxable_value
			else:
				tax_row[gst_rate]['igst_amount'] += (gst_rate / 100) * taxable_value
		else:
			if pos.tax_category == 'In-State':
				tax_row[gst_rate] = {
					'taxable_value': taxable_value,
					'cgst_rate': it.cgst_rate,
					'cgst_amount': round((it.cgst_rate / 100) * taxable_value, 2),
					'sgst_rate': it.sgst_rate,
					'sgst_amount': round((it.sgst_rate / 100) * taxable_value, 2),
					'igst_rate': 0,
					'igst_amount': 0
				}
			else:
				tax_row[gst_rate] = {
					'taxable_value': taxable_value,
					'cgst_rate': 0,
					'cgst_amount': 0,
					'sgst_rate': 0,
					'sgst_amount': 0,
					'igst_rate': gst_rate,
					'igst_amount': round((gst_rate / 100) * taxable_value, 2)
				}

	final_table = []
	for gst_rate, values in tax_row.items():
		if pos.tax_category == 'In-State':
			final_table.append([
				gst_rate,
				round(values['taxable_value'], 2),
				values['cgst_rate'],
				round(values['cgst_amount'], 2),
				values['sgst_rate'],
				round(values['sgst_amount'], 2),
				0,  # IGST Rate
				0   # IGST Amount
			])
		else:
			final_table.append([
				gst_rate,
				round(values['taxable_value'], 2),
				0,  # CGST Rate
				0,  # CGST Amount
				0,  # SGST Rate
				0,  # SGST Amount
				values['igst_rate'],
				round(values['igst_amount'], 2)
			])

	return {'tax_category': pos.tax_category, 'tax_rows': final_table}
