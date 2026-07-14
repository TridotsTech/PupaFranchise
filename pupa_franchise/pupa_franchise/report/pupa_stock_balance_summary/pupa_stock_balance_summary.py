# Copyright (c) 2026, Tridots and contributors
# For license information, please see license.txt

import frappe
import json
import requests


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "fieldname": "item_code",
            "label": "Item Code",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "item_name",
            "label": "Item Name",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "item_group",
            "label": "Item Group",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "warehouse",
            "label": "Warehouse",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "stock_uom",
            "label": "Stock UOM",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "actual_qty",
            "label": "Actual Qty",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "fieldname": "valuation_rate",
            "label": "Valuation Rate",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "stock_value",
            "label": "Stock Value",
            "fieldtype": "Currency",
            "width": 150
        }
    ]


def get_data(filters):
    warehouse = filters.get("warehouse")
    if not warehouse:
        return []

    try:
        from pupa_franchise.api.api_sync import get_api_settings
        base_url, headers = get_api_settings()

        response = requests.get(
            url=f"{base_url}/api/method/pupa.api.franchise.get_warehouse_stock_balance",
            headers=headers,
            params={"warehouse": warehouse}
        )

        if response.status_code != 200:
            frappe.msgprint(
                f"Error fetching stock from HQ. Status: {response.status_code}",
                indicator="red",
                alert=True
            )
            return []

        result = response.json().get("message", [])

        # Apply client-side filters
        item_group = filters.get("item_group")
        item_code = filters.get("item_code")

        if item_group:
            result = [r for r in result if r.get("item_group") and item_group.lower() in r["item_group"].lower()]

        if item_code:
            result = [r for r in result if r.get("item_code") and item_code.lower() in r["item_code"].lower()]

        return result

    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Pupa Stock Balance Summary Error"
        )
        frappe.msgprint(
            f"Error fetching stock data from HQ: {str(e)}",
            indicator="red",
            alert=True
        )
        return []
