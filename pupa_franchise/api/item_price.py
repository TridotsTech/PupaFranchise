import frappe
from erpnext.stock import get_item_details as eid


@frappe.whitelist()
def get_item_details(args, doc=None, for_validate=False, overwrite_warehouse=True):
    """
    Override of erpnext.stock.get_item_details.get_item_details
    Filters Item Price by custom_company to ensure each company
    only fetches its own price list rates in buying/selling transactions.
    """
    original_get_item_price = eid.get_item_price

    def company_filtered_get_item_price(args, item_code, ignore_party=False, force_batch_no=False):
        results = original_get_item_price(args, item_code, ignore_party, force_batch_no)
        company = args.get("company")

        if not company or not results:
            return results

        # Filter to Item Prices where custom_company matches the transaction company
        # or where custom_company is not set (generic prices)
        filtered = []
        for row in results:
            price_company = frappe.db.get_value("Item Price", row[0], "custom_company")
            if not price_company or price_company == company:
                filtered.append(row)

        # If company-specific prices found, return only those
        if filtered:
            return filtered

        # Fallback: return all results if no company-specific price exists
        return results

    eid.get_item_price = company_filtered_get_item_price
    try:
        result = eid.get_item_details(args, doc, for_validate, overwrite_warehouse)
    finally:
        # Always restore the original function
        eid.get_item_price = original_get_item_price

    return result
