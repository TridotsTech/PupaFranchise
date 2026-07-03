import frappe

def update_rate_based_on_discount(doc, method=None):
    if getattr(doc, "is_opening", None) != "Yes" and getattr(doc, "items", None):
        for row in doc.items:
            if getattr(row, "custom_mrp_discount_percentage", 0) != 0:
                ts_discount_amount = ((row.custom_mrp or 0) * (row.custom_mrp_discount_percentage or 0)) / 100
                discounted_price = (row.custom_mrp or 0) - ts_discount_amount
                
                # Reset standard discount fields to prevent double-discounting
                row.discount_percentage = 0
                row.discount_amount = 0
                
                row.rate = discounted_price
                row.custom_ts_discount_amount = ts_discount_amount
            else:
                if getattr(row, "custom_mrp", 0) == getattr(row, "price_list_rate", 0):
                    row.rate = row.custom_mrp
                    row.margin_rate_or_amount = 0
                    
        doc.calculate_taxes_and_totals()
