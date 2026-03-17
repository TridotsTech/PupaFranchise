# Copyright (c) 2025, Thirvusoft and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)

    if filters.from_date > filters.to_date:
        frappe.throw("From Date must be before To Date")

    return columns, data

def get_columns(filters):
    columns = [
        {"fieldname": "customer", "label": "Customer", "fieldtype": "Link", "options": "Customer", "width": 150},
        {"fieldname": "date", "label": "Date", "fieldtype": "Date", "width": 150},
        {"fieldname": "account", "label": "Account", "fieldtype": "Link", "options": "Account", "width": 150},
        {"fieldname": "credit", "label": "Credit", "fieldtype": "Float", "width": 150},
        {"fieldname": "debit", "label": "Debit", "fieldtype": "Float", "width": 150},
        {"fieldname": "voucher_type", "label": "Voucher Type", "fieldtype": "Data", "width": 150},
        {"fieldname": "voucher_no", "label": "Voucher No", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 250},
        {"label": "Linked Party","fieldname": "linked_party","fieldtype": "Data","width": 150}

    ]
    return columns


def get_data(filters):
    conditions = ["gl.is_cancelled = 0", "gl.is_opening = 'No'"]

    if filters.get("customer"):
        primary_party = filters["customer"]

        # Fetch linked suppliers (secondary parties) for this primary customer
        party_links = frappe.db.get_all(
            "Party Link",
            filters={"primary_party": primary_party, "primary_role": "Customer"},
            fields=["secondary_party", "secondary_role"]
        )

        secondary_parties = [link.secondary_party for link in party_links if link.secondary_role == "Supplier"]

        filters["primary_party"] = primary_party
        filters["secondary_parties"] = tuple(secondary_parties) if secondary_parties else ("__none__",)

        # Apply party and party_type filters with proper logic
        conditions.append("""
        (
          (gl.party = %(primary_party)s AND gl.party_type = 'Customer')
          OR
          (gl.party IN %(secondary_parties)s AND gl.party_type = 'Supplier')
        )
        """)

    # Other filters
    if filters.get("company"):
        conditions.append("gl.company = %(company)s")
    if filters.get("voucher_type"):
        conditions.append("gl.voucher_type = %(voucher_type)s")
    if filters.get("voucher_no"):
        conditions.append("gl.voucher_no = %(voucher_no)s")
    if filters.get("branch"):
        conditions.append("gl.branch = %(branch)s")
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append("gl.posting_date BETWEEN %(from_date)s AND %(to_date)s")

    conditions.append("""
        (
            gl.voucher_type != 'Journal Entry'
            OR EXISTS (
                SELECT 1 FROM `tabJournal Entry` je
                WHERE je.name = gl.voucher_no AND je.is_system_generated = 0
            )
        )
    """)
    
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT
            gl.posting_date AS date,
            gl.party AS customer,
            gl.account AS account,
            gl.voucher_type AS voucher_type,
            gl.voucher_no AS voucher_no,
            SUM(gl.debit) AS debit,
            SUM(gl.credit) AS credit,
            gl.party_type
        FROM
            `tabGL Entry` gl
        {where_clause}
        GROUP BY
            gl.voucher_no,
            gl.account,
            gl.party,
            gl.posting_date,
            gl.voucher_type,
            gl.party_type
        ORDER BY
            gl.posting_date
    """

    ledger_to_fetch = frappe.db.sql(query, filters, as_dict=True)
    final_results = []

    if filters.get("secondary_parties"):
        # Use primary and secondary parties for grouping

        opening_debit, opening_credit = fetch_opening_balance(filters)
        opening_balance = opening_debit - opening_credit
        closing_balance = fetch_closing_balance(filters)
        current_debit, current_credit = fetch_current_total(filters)
        current_total = current_debit - current_credit

        if not opening_balance and not closing_balance and not current_total and not ledger_to_fetch:
            return []

        # Header for primary customer
        final_results.append({
            'indent': 0,
            'customer': filters["primary_party"],
            'debit': 0,
            'credit': 0
        })

        # Append ledger transactions of both primary and secondary parties
        if ledger_to_fetch:
            for transaction in ledger_to_fetch:
                transaction['indent'] = 1
                final_results.append(transaction)
        else:
            final_results.append({
                'indent': 1,
                'voucher_no': 'No transactions',
                'debit': 0,
                'credit': 0
            })

        # Totals summary
        final_results.append({
            'indent': 1,
            'account': 'Opening Balance',
            'debit': opening_debit,
            'credit': opening_credit,
            'is_total': 1
        })
        final_results.append({
            'indent': 1,
            'account': 'Total',
            'debit': current_debit,
            'credit': current_credit,
            'is_total': 1
        })
        final_results.append({
            'indent': 1,
            'account': 'Closing Balance',
            'debit': opening_balance + current_total if (opening_balance + current_total) > 0 else 0,
            'credit': -(opening_balance + current_total) if (opening_balance + current_total) < 0 else 0,
            'is_total': 1
        })

    else:
        # No linked parties: fallback logic (unchanged)
        customer_list = frappe.db.sql("""SELECT name FROM `tabCustomer`""", as_dict=True)
        customer_names = [c["name"] for c in customer_list]

        for party in customer_names:
            customer_filters = filters.copy()
            customer_filters["customer"] = party

            opening_debit, opening_credit = fetch_opening_balance(customer_filters)
            opening_balance = opening_debit - opening_credit
            closing_balance = fetch_closing_balance(customer_filters)
            current_debit, current_credit = fetch_current_total(customer_filters)
            current_total = current_debit - current_credit

            if not opening_balance and not closing_balance and not current_total:
                continue

            final_results.append({
                'indent': 0,
                'customer': party,
                'debit': 0,
                'credit': 0
            })

            party_ledger = [row for row in ledger_to_fetch if row['customer'] == party]
            if party_ledger:
                for transaction in party_ledger:
                    transaction['indent'] = 1
                    final_results.append(transaction)
            else:
                final_results.append({
                    'indent': 1,
                    'voucher_no': 'No transactions',
                    'debit': 0,
                    'credit': 0
                })

            final_results.append({
                'indent': 1,
                'account': 'Opening Balance',
                'debit': opening_debit,
                'credit': opening_credit,
                'is_total': 1
            })
            final_results.append({
                'indent': 1,
                'account': 'Total',
                'debit': current_debit,
                'credit': current_credit,
                'is_total': 1
            })
            final_results.append({
                'indent': 1,
                'account': 'Closing Balance',
                'debit': opening_balance + current_total if (opening_balance + current_total) > 0 else 0,
                'credit': -(opening_balance + current_total) if (opening_balance + current_total) < 0 else 0,
                'is_total': 1
            })

    
    return final_results



def fetch_opening_balance(filters):
    opening_condition = ["gl.is_cancelled = 0"]

    if filters.get("company"):
        opening_condition.append("gl.company = %(company)s")
    if filters.get("voucher_type"):
        opening_condition.append("gl.voucher_type = %(voucher_type)s")
    if filters.get("voucher_no"):
        opening_condition.append("gl.voucher_no = %(voucher_no)s")

    # Opening includes entries before from_date or marked opening
    if filters.get("from_date"):
        opening_condition.append("(gl.posting_date < %(from_date)s OR gl.is_opening = 'Yes')")

    if filters.get("secondary_parties") and filters.get("primary_party"):
        # Same filtering logic as main query
        opening_condition.append("""
        (
          (gl.party = %(primary_party)s AND gl.party_type = 'Customer')
          OR
          (gl.party IN %(secondary_parties)s AND gl.party_type = 'Supplier')
        )
        """)
    elif filters.get("customer"):
        opening_condition.append("gl.party = %(customer)s")
        opening_condition.append("gl.party_type = 'Customer'")
    else:
        opening_condition.append("gl.party IS NOT NULL")

    query = f"""
        SELECT 
            SUM(gl.debit) AS total_debit, 
            SUM(gl.credit) AS total_credit
        FROM `tabGL Entry` gl
        WHERE {' AND '.join(opening_condition)}
    """

    result = frappe.db.sql(query, filters, as_dict=True)

    if result and result[0]:
        debit = result[0].get("total_debit") or 0
        credit = result[0].get("total_credit") or 0
        return debit, credit

    return 0, 0


def fetch_closing_balance(filters):
    closing_condition = ["gl.is_cancelled = 0"]

    if filters.get("company"):
        closing_condition.append("gl.company = %(company)s")
    if filters.get("voucher_type"):
        closing_condition.append("gl.voucher_type = %(voucher_type)s")
    if filters.get("voucher_no"):
        closing_condition.append("gl.voucher_no = %(voucher_no)s")
    if filters.get("to_date"):
        closing_condition.append("gl.posting_date <= %(to_date)s")
    if filters.get("branch"):
        closing_condition.append("gl.branch = %(branch)s")

    if filters.get("secondary_parties") and filters.get("primary_party"):
        closing_condition.append("""
        (
          (gl.party = %(primary_party)s AND gl.party_type = 'Customer')
          OR
          (gl.party IN %(secondary_parties)s AND gl.party_type = 'Supplier')
        )
        """)
    elif filters.get("customer"):
        closing_condition.append("gl.party = %(customer)s")
        closing_condition.append("gl.party_type = 'Customer'")

    query = f"""
        SELECT 
            SUM(gl.debit) AS total_debit, 
            SUM(gl.credit) AS total_credit
        FROM `tabGL Entry` gl
        WHERE {' AND '.join(closing_condition)}
    """

    result = frappe.db.sql(query, filters, as_dict=True)
    if result and result[0]:
        debit = result[0].get("total_debit") or 0
        credit = result[0].get("total_credit") or 0
        return debit - credit

    return 0


def fetch_current_total(filters):
    conditions = ["gl.is_cancelled = 0", "gl.is_opening = 'No'"]
    conditions.append("""
        (
            gl.voucher_type != 'Journal Entry'
            OR EXISTS (
                SELECT 1 FROM `tabJournal Entry` je
                WHERE je.name = gl.voucher_no AND je.is_system_generated = 0
            )
        )
    """)

    if filters.get("company"):
        conditions.append("gl.company = %(company)s")
    if filters.get("voucher_type"):
        conditions.append("gl.voucher_type = %(voucher_type)s")
    if filters.get("voucher_no"):
        conditions.append("gl.voucher_no = %(voucher_no)s")
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append("gl.posting_date BETWEEN %(from_date)s AND %(to_date)s")
    if filters.get("branch"):
        conditions.append("gl.branch = %(branch)s")

    if filters.get("secondary_parties") and filters.get("primary_party"):
        conditions.append("""
        (
          (gl.party = %(primary_party)s AND gl.party_type = 'Customer')
          OR
          (gl.party IN %(secondary_parties)s AND gl.party_type = 'Supplier')
        )
        """)
    elif filters.get("customer"):
        conditions.append("gl.party = %(customer)s")
        conditions.append("gl.party_type = 'Customer'")
    else:
        conditions.append("gl.party IS NOT NULL")

    query = f"""
        SELECT 
            SUM(gl.debit) AS total_debit, 
            SUM(gl.credit) AS total_credit
        FROM `tabGL Entry` gl
        WHERE {' AND '.join(conditions)}
    """

    result = frappe.db.sql(query, filters, as_dict=True)
    if result and result[0]:
        debit = result[0].get("total_debit") or 0
        credit = result[0].get("total_credit") or 0
        return debit, credit

    return 0, 0


@frappe.whitelist()
def company_address(company):
    if not company:
        return
    address_links = frappe.db.get_all(
        "Dynamic Link",
        filters={
            "link_doctype": "Company",
            "link_name": company,
            "parenttype": "Address"
        },
        fields=["parent"]
    )
    for link in address_links:
        doc = frappe.get_doc("Address", link.parent)
        if doc.is_primary_address:
            return doc.address_line1, doc.address_line2, doc.city, doc.pincode
    return ""


@frappe.whitelist()
def party_address(party, party_type="Customer"):
    if not party or not party_type:
        return

    address_links = frappe.db.get_all(
        "Dynamic Link",
        filters={
            "link_doctype": party_type,
            "link_name": party,
            "parenttype": "Address"
        },
        fields=["parent"]
    )

    for link in address_links:
        address = frappe.get_doc("Address", link.parent)
        if address.is_primary_address:
            return address.address_line1, address.address_line2, address.city, address.pincode, address.gstin

    return ""
