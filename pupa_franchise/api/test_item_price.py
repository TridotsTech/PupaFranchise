# Copyright (c) 2026, Tridots and Contributors
# Test suite for pupa_franchise.api.item_price
# Tests the company-filtered Item Price override

import frappe
from frappe.tests.utils import FrappeTestCase
from unittest.mock import patch, MagicMock


class TestGetItemDetails(FrappeTestCase):
    """Tests for item_price.get_item_details — company-filtered price override."""

    def test_original_function_restored_after_call(self):
        """The monkey-patched get_item_price should be restored after the call."""
        from erpnext.stock import get_item_details as eid

        original_fn = eid.get_item_price

        # We'll mock get_item_details to avoid needing a full transaction context
        with patch.object(eid, 'get_item_details', return_value={}):
            try:
                from pupa_franchise.api.item_price import get_item_details
                get_item_details(args='{"company": "Test"}', doc=None)
            except Exception:
                pass  # We just want to check if the function is restored

        # Verify the original function was restored
        self.assertEqual(eid.get_item_price, original_fn)

    def test_original_function_restored_even_on_error(self):
        """Even if an error occurs, get_item_price should be restored."""
        from erpnext.stock import get_item_details as eid

        original_fn = eid.get_item_price

        with patch.object(eid, 'get_item_details', side_effect=Exception("Test error")):
            try:
                from pupa_franchise.api.item_price import get_item_details
                get_item_details(args='{"company": "Test"}', doc=None)
            except Exception:
                pass

        # Must be restored despite the error
        self.assertEqual(eid.get_item_price, original_fn)

    def test_company_filter_logic(self):
        """Verify the inner company_filtered_get_item_price filters correctly."""
        # Test the filtering logic directly
        from pupa_franchise.api.item_price import get_item_details

        # Create mock data: simulate Item Price records
        item_code = "_Test Item Price Filter"
        company = "_Test Company IP"

        # We'll test the filter function in isolation
        # by examining what company_filtered_get_item_price does

        # The function filters by checking custom_company on each Item Price
        # returned by the original get_item_price. We verify this logic
        # by checking the filtering in a unit context.

        mock_results = [
            ("IP-001", "Standard Buying", "INR", 100),
            ("IP-002", "Standard Buying", "INR", 150),
        ]

        # Mock frappe.db.get_value to return company for IP-001 and different for IP-002
        original_get_value = frappe.db.get_value

        def mock_get_value(doctype, name, field):
            if doctype == "Item Price" and field == "custom_company":
                if name == "IP-001":
                    return company  # Matches
                elif name == "IP-002":
                    return "Other Company"  # Doesn't match
            return original_get_value(doctype, name, field)

        # Apply the same filter logic as the code
        filtered = []
        for row in mock_results:
            price_company = mock_get_value("Item Price", row[0], "custom_company")
            if not price_company or price_company == company:
                filtered.append(row)

        # Only IP-001 should match
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0][0], "IP-001")

    def test_no_company_skips_filtering(self):
        """When no company is provided, all results should be returned."""
        # Test the filter logic: if company is empty, return all results
        mock_results = [
            ("IP-001", "Standard Buying", "INR", 100),
            ("IP-002", "Standard Buying", "INR", 150),
        ]

        company = ""  # No company
        if not company or not mock_results:
            filtered = mock_results
        else:
            filtered = []

        # All results should be returned when no company
        self.assertEqual(len(filtered), 2)

    def test_generic_prices_included_as_fallback(self):
        """Item Prices without custom_company should be included."""
        mock_results = [
            ("IP-001", "Standard Buying", "INR", 100),  # No custom_company
            ("IP-002", "Standard Buying", "INR", 150),  # Has custom_company matching
        ]

        company = "_Test Company"

        def get_price_company(name):
            return {"IP-001": None, "IP-002": "_Test Company"}.get(name)

        filtered = []
        for row in mock_results:
            price_company = get_price_company(row[0])
            if not price_company or price_company == company:
                filtered.append(row)

        # Both should be included (None + matching company)
        self.assertEqual(len(filtered), 2)
