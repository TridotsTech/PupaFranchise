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
        args_dict = frappe.parse_json(args) or {}
        item_code = args_dict.get("item_code")
        if result and isinstance(result, dict) and item_code:
            company = args_dict.get("company")
            currency = args_dict.get("currency") or result.get("currency")
            mrp_rate = get_mrp_rate(item_code, company, currency)
            if mrp_rate:
                result["custom_mrp"] = mrp_rate
    finally:
        # Always restore the original function
        eid.get_item_price = original_get_item_price

    return result


def get_mrp_rate(item_code, company=None, currency=None):
    """
    Fetches the price from the 'MRP' price list for a given item,
    matching the company-specific price list rate if available,
    falling back to a generic price (without company).
    """
    if not item_code:
        return 0.0

    filters = {
        "item_code": item_code,
        "price_list": "MRP"
    }
    if currency:
        filters["currency"] = currency

    item_prices = frappe.get_all(
        "Item Price",
        filters=filters,
        fields=["price_list_rate", "custom_company"],
        order_by="custom_company desc"
    )

    if not item_prices:
        return 0.0

    if company:
        for ip in item_prices:
            if ip.custom_company == company:
                return ip.price_list_rate

    for ip in item_prices:
        if not ip.custom_company:
            return ip.price_list_rate

    return 0.0

