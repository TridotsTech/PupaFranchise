# Copyright (c) 2026, Tridots and Contributors
# Test suite for pupa_franchise.utils.py.purchase_order
# Tests PO credentials helper (branch and default supplier lookup)

import frappe
from frappe.tests.utils import FrappeTestCase


class TestGetPurchaseOrderCredentials(FrappeTestCase):
    """Tests for purchase_order.get_purchase_order_credentials —
    returns branch and default supplier for a given company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._ensure_test_data()

    @classmethod
    def _ensure_test_data(cls):
        """Create test company with custom_branch and ensure settings."""
        # Create a test branch
        cls.branch_name = "_Test PO Branch"
        cls.address_name = "_Test Branch Address"

        # Check by address_title instead of name
        existing_address = frappe.db.get_value("Address", {"address_title": cls.address_name}, "name")
        if not existing_address:
            addr = frappe.get_doc({
                "doctype": "Address",
                "address_title": cls.address_name,
                "address_line1": "Test Address Line 1",
                "city": "Test City",
                "country": "India"
            }).insert(ignore_permissions=True)
            cls.address_doc_name = addr.name
        else:
            cls.address_doc_name = existing_address

        if not frappe.db.exists("Branch", cls.branch_name):
            frappe.get_doc({
                "doctype": "Branch",
                "branch": cls.branch_name,
                "custom_address": cls.address_doc_name
            }).insert(ignore_permissions=True)

        # Create a company with custom_branch
        cls.company_with_branch = "_Test Company With Branch"
        if not frappe.db.exists("Company", cls.company_with_branch):
            company = frappe.get_doc({
                "doctype": "Company",
                "company_name": cls.company_with_branch,
                "default_currency": "INR",
                "country": "India",
            })
            company.insert(ignore_permissions=True)
        # Set custom_branch
        frappe.db.set_value("Company", cls.company_with_branch,
            "custom_branch", cls.branch_name)

        # Company without branch
        cls.company_no_branch = "_Test Company No Branch"
        if not frappe.db.exists("Company", cls.company_no_branch):
            company = frappe.get_doc({
                "doctype": "Company",
                "company_name": cls.company_no_branch,
                "default_currency": "INR",
                "country": "India",
            })
            company.insert(ignore_permissions=True)
        frappe.db.set_value("Company", cls.company_no_branch,
            "custom_branch", None)

        frappe.db.commit()

    def test_no_company_returns_none(self):
        """Calling without company should return None."""
        from pupa_franchise.utils.py.purchase_order import get_purchase_order_credentials

        result = get_purchase_order_credentials(company=None)
        self.assertIsNone(result)

    def test_company_with_branch_returns_success(self):
        """Company with custom_branch should return branch with success status."""
        from pupa_franchise.utils.py.purchase_order import get_purchase_order_credentials

        result = get_purchase_order_credentials(company=self.company_with_branch)

        self.assertIsNotNone(result)
        self.assertEqual(result["status_1"], "success")
        self.assertEqual(result["response_1"], self.branch_name)

    def test_company_without_branch_returns_failure(self):
        """Company without custom_branch should return failure status."""
        from pupa_franchise.utils.py.purchase_order import get_purchase_order_credentials

        result = get_purchase_order_credentials(company=self.company_no_branch)

        self.assertIsNotNone(result)
        self.assertEqual(result["status_1"], "failure")
        self.assertIn("Branch is not mapped", result["response_1"])

    def test_default_supplier_from_settings(self):
        """Should return default supplier from Franchise Settings."""
        from pupa_franchise.utils.py.purchase_order import get_purchase_order_credentials

        default_supplier = frappe.db.get_single_value(
            "Franchise Settings", "default_supplier"
        )

        result = get_purchase_order_credentials(company=self.company_with_branch)

        if default_supplier:
            self.assertEqual(result["status_2"], "success")
            self.assertEqual(result["response_2"], default_supplier)
        else:
            self.assertEqual(result["status_2"], "failure")
            self.assertIn("Default supplier is not mapped", result["response_2"])

    def test_response_has_all_keys(self):
        """Response should always contain response_1, status_1, response_2, status_2."""
        from pupa_franchise.utils.py.purchase_order import get_purchase_order_credentials

        result = get_purchase_order_credentials(company=self.company_with_branch)

        self.assertIsNotNone(result)
        self.assertIn("response_1", result)
        self.assertIn("status_1", result)
        self.assertIn("response_2", result)
        self.assertIn("status_2", result)
