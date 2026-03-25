import frappe
from frappe.utils import flt

def get_tax_table_sales_invoice(doctype, doc):
    pos = frappe.get_cached_doc(doctype, doc)
    tax_row = {}

    for it in pos.items:
        # Check if the fields exist; if not, use 0
        cgst_rate = flt(getattr(it, 'cgst_rate', 0))
        sgst_rate = flt(getattr(it, 'sgst_rate', 0))
        igst_rate = flt(getattr(it, 'igst_rate', 0))
        
        if pos.tax_category == 'In-State':
            gst_rate = cgst_rate + sgst_rate
        else:
            gst_rate = igst_rate

        taxable_value = flt(it.net_amount)
        if gst_rate == 0:
            continue  # Skip if no GST applies

        if gst_rate in tax_row:
            tax_row[gst_rate]['taxable_value'] += taxable_value
            if pos.tax_category == 'In-State':
                tax_row[gst_rate]['cgst_amount'] += (cgst_rate / 100) * taxable_value
                tax_row[gst_rate]['sgst_amount'] += (sgst_rate / 100) * taxable_value
            else:
                tax_row[gst_rate]['igst_amount'] += (gst_rate / 100) * taxable_value
        else:
            if pos.tax_category == 'In-State':
                tax_row[gst_rate] = {
                    'taxable_value': taxable_value,
                    'cgst_rate': cgst_rate,
                    'cgst_amount': round((cgst_rate / 100) * taxable_value, 2),
                    'sgst_rate': sgst_rate,
                    'sgst_amount': round((sgst_rate / 100) * taxable_value, 2),
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
                    'igst_rate': igst_rate,
                    'igst_amount': round((igst_rate / 100) * taxable_value, 2)
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

    return {'tax_category': getattr(pos, 'tax_category', 'In-State'), 'tax_rows': final_table}
