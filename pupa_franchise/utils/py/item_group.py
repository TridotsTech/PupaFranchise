import frappe
from frappe import _


def on_update(doc, method=None):
    frappe.enqueue(
        "pupa_franchise.utils.py.item_group.sync_defaults_to_items",
        doc_name=doc.name,
        queue="long",
        timeout=600,
        enqueue_after_commit=True
    )


def sync_defaults_to_items(doc_name):
    doc = frappe.get_doc("Item Group", doc_name)

    group_defaults = doc.get("item_group_defaults") or []

    # ✅ Start message (only once)
    frappe.publish_realtime("msgprint", {
        "message": f"Sync started for {doc_name}",
        "title": "Item Sync",
        "indicator": "blue"
    })

    group_map = {
        d.company.strip(): d for d in group_defaults if d.company
    }

    items = frappe.get_all(
        "Item",
        filters={"item_group": doc_name},
        pluck="name"
    )

    if not items:
        frappe.publish_realtime("msgprint", {
            "message": f"No items found in {doc_name}",
            "indicator": "orange"
        })
        return

    updated_count = 0

    for item_name in items:
        item_doc = frappe.get_doc("Item", item_name)
        existing_rows = item_doc.get("item_defaults") or []

        modified = False
        new_item_defaults = []

        # --- UPDATE / REMOVE ---
        for row in existing_rows:
            comp_id = row.company.strip() if row.company else ""

            if comp_id in group_map:
                g_row = group_map[comp_id]

                if (
                    row.default_warehouse != g_row.default_warehouse or
                    row.default_price_list != g_row.default_price_list
                ):
                    row.default_warehouse = g_row.default_warehouse
                    row.default_price_list = g_row.default_price_list
                    modified = True

                new_item_defaults.append(row)

            else:
                # ❌ REMOVE
                modified = True

        # --- ADD MISSING ---
        current_companies = [
            r.company.strip() for r in new_item_defaults if r.company
        ]

        for comp_id, g_row in group_map.items():
            if comp_id not in current_companies:
                new_item_defaults.append({
                    "doctype": "Item Default",
                    "company": g_row.company,
                    "default_warehouse": g_row.default_warehouse,
                    "default_price_list": g_row.default_price_list
                })
                modified = True

        # --- SAVE ---
        if modified:
            item_doc.set("item_defaults", new_item_defaults)
            item_doc.flags.ignore_mandatory = True
            item_doc.flags.ignore_links = True
            item_doc.save(ignore_permissions=True)
            updated_count += 1

    # ✅ Final message
    frappe.publish_realtime("msgprint", {
        "message": f"{updated_count} items updated in {doc_name}",
        "title": "Sync Completed",
        "indicator": "green"
    })

    # ✅ Proper logging
    frappe.logger().info(
        f"Item Group Sync: {updated_count} items updated for {doc_name}"
    )