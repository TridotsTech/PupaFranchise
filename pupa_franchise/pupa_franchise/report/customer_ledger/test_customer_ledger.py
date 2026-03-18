# Copyright (c) 2026, Tridots and Contributors
# Test suite for pupa_franchise.pupa_franchise.report.customer_ledger
# Tests Customer Ledger report columns, data, balances, and address helpers

import frappe
from frappe.tests.utils import FrappeTestCase


class TestCustomerLedgerReport(FrappeTestCase):
    """Tests for the Customer Ledger report."""

    def test_get_columns_returns_correct_fields(self):
        """get_columns should return the expected column definitions."""
        from pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger import get_columns

        filters = frappe._dict({})
        columns = get_columns(filters)

        self.assertIsInstance(columns, list)
        self.assertTrue(len(columns) > 0)

        # Check required columns exist
        fieldnames = [c["fieldname"] for c in columns]
        self.assertIn("customer", fieldnames)
        self.assertIn("date", fieldnames)
        self.assertIn("account", fieldnames)
        self.assertIn("credit", fieldnames)
        self.assertIn("debit", fieldnames)
        self.assertIn("voucher_type", fieldnames)
        self.assertIn("voucher_no", fieldnames)
        self.assertIn("linked_party", fieldnames)

    def test_get_columns_correct_fieldtypes(self):
        """Columns should have correct fieldtypes."""
        from pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger import get_columns

        columns = get_columns(frappe._dict({}))

        type_map = {c["fieldname"]: c["fieldtype"] for c in columns}
        self.assertEqual(type_map["customer"], "Link")
        self.assertEqual(type_map["date"], "Date")
        self.assertEqual(type_map["credit"], "Float")
        self.assertEqual(type_map["debit"], "Float")
        self.assertEqual(type_map["voucher_no"], "Dynamic Link")

    def test_date_validation_from_after_to(self):
        """from_date > to_date should throw an error."""
        from pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger import execute

        filters = frappe._dict({
            "from_date": "2026-12-31",
            "to_date": "2026-01-01",
            "company": frappe.db.get_value("Company", {}, "name") or "Test",
        })

        with self.assertRaises(Exception):
            execute(filters)

    def test_execute_returns_columns_and_data(self):
        """execute() should return a tuple of (columns, data)."""
        from pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger import execute

        company = frappe.db.get_value("Company", {}, "name")
        if not company:
            self.skipTest("No company found")

        filters = frappe._dict({
            "from_date": "2026-01-01",
            "to_date": "2026-12-31",
            "company": company,
        })

        result = execute(filters)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

        columns, data = result
        self.assertIsInstance(columns, list)
        self.assertIsInstance(data, list)

    def test_get_data_with_company_filter(self):
        """get_data with company filter should not raise errors."""
        from pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger import get_data

        company = frappe.db.get_value("Company", {}, "name")
        if not company:
            self.skipTest("No company found")

        filters = frappe._dict({
            "from_date": "2026-01-01",
            "to_date": "2026-12-31",
            "company": company,
        })

        # Should not raise any errors
        data = get_data(filters)
        self.assertIsInstance(data, list)

    def test_get_data_with_customer_filter(self):
        """get_data with customer filter should use party link logic."""
        from pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger import get_data

        company = frappe.db.get_value("Company", {}, "name")
        customer = frappe.db.get_value("Customer", {}, "name")
        if not company or not customer:
            self.skipTest("No company or customer found")

        filters = frappe._dict({
            "from_date": "2026-01-01",
            "to_date": "2026-12-31",
            "company": company,
            "customer": customer,
        })

        data = get_data(filters)
        self.assertIsInstance(data, list)

    def test_fetch_opening_balance_returns_tuple(self):
        """fetch_opening_balance should return (debit, credit) tuple."""
        from pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger import fetch_opening_balance

        company = frappe.db.get_value("Company", {}, "name")
        if not company:
            self.skipTest("No company found")

        filters = frappe._dict({
            "from_date": "2026-01-01",
            "company": company,
        })

        result = fetch_opening_balance(filters)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_fetch_closing_balance_returns_number(self):
        """fetch_closing_balance should return a number."""
        from pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger import fetch_closing_balance

        company = frappe.db.get_value("Company", {}, "name")
        if not company:
            self.skipTest("No company found")

        filters = frappe._dict({
            "to_date": "2026-12-31",
            "company": company,
        })

        result = fetch_closing_balance(filters)
        self.assertIsInstance(result, (int, float))

    def test_fetch_current_total_returns_tuple(self):
        """fetch_current_total should return (debit, credit) tuple."""
        from pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger import fetch_current_total

        company = frappe.db.get_value("Company", {}, "name")
        if not company:
            self.skipTest("No company found")

        filters = frappe._dict({
            "from_date": "2026-01-01",
            "to_date": "2026-12-31",
            "company": company,
        })

        result = fetch_current_total(filters)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)


class TestCustomerLedgerAddressHelpers(FrappeTestCase):
    """Tests for address helper functions in customer_ledger."""

    def test_company_address_returns_empty_for_no_company(self):
        """company_address(None) should return None."""
        from pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger import company_address

        result = company_address(None)
        self.assertIsNone(result)

    def test_company_address_returns_data_or_empty(self):
        """company_address should return address tuple or empty string."""
        from pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger import company_address

        company = frappe.db.get_value("Company", {}, "name")
        if not company:
            self.skipTest("No company found")

        result = company_address(company)
        # Should be either a tuple of address fields or empty string
        self.assertTrue(
            result == "" or (isinstance(result, tuple) and len(result) == 4),
            f"Expected empty string or 4-tuple, got: {result}"
        )

    def test_party_address_returns_none_for_no_party(self):
        """party_address(None) should return None."""
        from pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger import party_address

        result = party_address(None)
        self.assertIsNone(result)

    def test_party_address_returns_data_or_empty(self):
        """party_address should return address tuple or empty string."""
        from pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger import party_address

        customer = frappe.db.get_value("Customer", {}, "name")
        if not customer:
            self.skipTest("No customer found")

        result = party_address(customer, party_type="Customer")
        # Should be either a tuple of 5 address fields or empty string
        self.assertTrue(
            result == "" or (isinstance(result, tuple) and len(result) == 5),
            f"Expected empty string or 5-tuple, got: {result}"
        )

    def test_party_address_no_party_type_returns_none(self):
        """party_address with no party_type should return None."""
        from pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger import party_address

        result = party_address("Test Customer", party_type=None)
        self.assertIsNone(result)
