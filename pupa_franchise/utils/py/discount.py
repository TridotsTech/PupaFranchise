import frappe
from frappe.utils import flt

def update_rate_based_on_discount(doc, method=None):
    if getattr(doc, "is_opening", None) != "Yes" and getattr(doc, "items", None):
        for row in doc.items:
            custom_mrp = flt(row.custom_mrp)
            discount_percentage = flt(row.custom_mrp_discount_percentage)
            price_list_rate = flt(row.price_list_rate)

            if discount_percentage != 0:
                ts_discount_amount = (custom_mrp * discount_percentage) / 100
                discounted_price = custom_mrp - ts_discount_amount
                
                # Reset standard discount fields to prevent double-discounting
                row.discount_percentage = 0
                row.discount_amount = 0
                
                row.rate = discounted_price
                row.custom_ts_discount_amount = ts_discount_amount
            else:
                if custom_mrp == price_list_rate:
                    row.rate = custom_mrp
                    row.margin_rate_or_amount = 0
                    
        doc.calculate_taxes_and_totals()

