# Copyright (c) 2026, Tridots and Contributors
# Test suite for pupa_franchise.api.permission
# Tests company-based user restrictions and record-level access control

import frappe
from frappe.tests.utils import FrappeTestCase


class TestPermissionQueryConditions(FrappeTestCase):
    """Tests for get_permission_query_conditions — SQL WHERE clauses
    that restrict list views based on user's allowed companies."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._ensure_test_companies()
        cls._ensure_test_user()

    @classmethod
    def _ensure_test_companies(cls):
        """Create test companies if they don't exist."""
        for company_name in ["_Test Franchise A", "_Test Franchise B"]:
            if not frappe.db.exists("Company", company_name):
                company = frappe.get_doc({
                    "doctype": "Company",
                    "company_name": company_name,
                    "default_currency": "INR",
                    "country": "India",
                })
                company.insert(ignore_permissions=True)
        frappe.db.commit()

    @classmethod
    def _ensure_test_user(cls):
        """Create a test user with company restrictions."""
        test_email = "test_franchise_user@example.com"
        if not frappe.db.exists("User", test_email):
            user = frappe.get_doc({
                "doctype": "User",
                "email": test_email,
                "first_name": "Test Franchise",
                "user_type": "System User",
                "send_welcome_email": 0,
                "roles": [{"role": "Stock User"}, {"role": "Accounts User"}],
            })
            user.insert(ignore_permissions=True)

        # Set user permission: only _Test Franchise A
        existing = frappe.db.exists("User Permission", {
            "user": test_email,
            "allow": "Company",
            "for_value": "_Test Franchise A"
        })
        if not existing:
            frappe.get_doc({
                "doctype": "User Permission",
                "user": test_email,
                "allow": "Company",
                "for_value": "_Test Franchise A",
            }).insert(ignore_permissions=True)
        frappe.db.commit()

    def test_administrator_gets_empty_conditions(self):
        """Administrator should always get empty conditions (no restrictions)."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        result = get_permission_query_conditions("Administrator", "Sales Order")
        self.assertEqual(result, "")

    def test_system_manager_gets_empty_conditions(self):
        """System Manager role should bypass all restrictions."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        # Find or use a System Manager user
        admin_users = frappe.get_all("Has Role", filters={
            "role": "System Manager", "parenttype": "User"
        }, fields=["parent"], limit=1)

        if admin_users:
            result = get_permission_query_conditions(admin_users[0].parent, "Sales Order")
            self.assertEqual(result, "")

    def test_company_restricted_user_gets_sql_condition(self):
        """User restricted to a company should get SQL WHERE clause."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        test_email = "test_franchise_user@example.com"
        result = get_permission_query_conditions(test_email, "Sales Order")

        # Should contain company filter with the allowed company
        self.assertIn("_Test Franchise A", result)
        self.assertIn("`tabSales Order`.company IN", result)

    def test_company_filter_for_purchase_order(self):
        """Purchase Order should be filtered by company field."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        test_email = "test_franchise_user@example.com"
        result = get_permission_query_conditions(test_email, "Purchase Order")

        self.assertIn("`tabPurchase Order`.company IN", result)
        self.assertIn("_Test Franchise A", result)

    def test_company_filter_for_sales_invoice(self):
        """Sales Invoice should be filtered by company field."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        test_email = "test_franchise_user@example.com"
        result = get_permission_query_conditions(test_email, "Sales Invoice")

        self.assertIn("`tabSales Invoice`.company IN", result)

    def test_company_filter_for_purchase_invoice(self):
        """Purchase Invoice should be filtered by company."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        test_email = "test_franchise_user@example.com"
        result = get_permission_query_conditions(test_email, "Purchase Invoice")

        self.assertIn("`tabPurchase Invoice`.company IN", result)

    def test_bin_special_handling(self):
        """Bin should be filtered by warehouse's company, not a direct company field."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        test_email = "test_franchise_user@example.com"
        result = get_permission_query_conditions(test_email, "Bin")

        # Should use subquery on Warehouse
        self.assertIn("`tabBin`.warehouse IN", result)
        self.assertIn("SELECT name FROM tabWarehouse", result)
        self.assertIn("_Test Franchise A", result)

    def test_customer_filtering_via_child_table(self):
        """Customer should be filtered via Allowed Company User Table child table."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        test_email = "test_franchise_user@example.com"
        result = get_permission_query_conditions(test_email, "Customer")

        self.assertIn("`tabCustomer`.name IN", result)
        self.assertIn("tabAllowed Company User Table", result)
        self.assertIn("_Test Franchise A", result)

    def test_item_price_strict_company_filter(self):
        """Item Price should be filtered strictly by custom_company."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        test_email = "test_franchise_user@example.com"
        result = get_permission_query_conditions(test_email, "Item Price")

        # Strict filter: only items with matching custom_company
        self.assertIn("`tabItem Price`.custom_company IN", result)
        self.assertIn("_Test Franchise A", result)

    def test_no_user_permissions_returns_empty(self):
        """User without company restrictions should get empty conditions."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        # Create or use a user without company restrictions
        no_restriction_email = "test_no_restriction@example.com"
        if not frappe.db.exists("User", no_restriction_email):
            frappe.get_doc({
                "doctype": "User",
                "email": no_restriction_email,
                "first_name": "No Restriction",
                "user_type": "System User",
                "send_welcome_email": 0,
                "roles": [{"role": "Stock User"}],
            }).insert(ignore_permissions=True)
            frappe.db.commit()

        result = get_permission_query_conditions(no_restriction_email, "Sales Order")
        self.assertEqual(result, "")

    def test_no_doctype_returns_empty(self):
        """Missing doctype should return empty conditions."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        result = get_permission_query_conditions("test_franchise_user@example.com", None)
        self.assertEqual(result, "")

    def test_gl_entry_filtered_by_company(self):
        """GL Entry should be filtered by company field."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        test_email = "test_franchise_user@example.com"
        result = get_permission_query_conditions(test_email, "GL Entry")

        self.assertIn("`tabGL Entry`.company IN", result)

    def test_payment_entry_filtered_by_company(self):
        """Payment Entry should be filtered by company field."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        test_email = "test_franchise_user@example.com"
        result = get_permission_query_conditions(test_email, "Payment Entry")

        self.assertIn("`tabPayment Entry`.company IN", result)

    def test_journal_entry_filtered_by_company(self):
        """Journal Entry should be filtered by company field."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        test_email = "test_franchise_user@example.com"
        result = get_permission_query_conditions(test_email, "Journal Entry")

        self.assertIn("`tabJournal Entry`.company IN", result)

    def test_stock_ledger_entry_filtered_by_company(self):
        """Stock Ledger Entry should be filtered by company field."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        test_email = "test_franchise_user@example.com"
        result = get_permission_query_conditions(test_email, "Stock Ledger Entry")

        self.assertIn("`tabStock Ledger Entry`.company IN", result)

    def test_warehouse_filtered_by_company(self):
        """Warehouse should be filtered by company field."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        test_email = "test_franchise_user@example.com"
        result = get_permission_query_conditions(test_email, "Warehouse")

        self.assertIn("`tabWarehouse`.company IN", result)

    def test_delivery_note_filtered_by_company(self):
        """Delivery Note should be filtered by company field."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        test_email = "test_franchise_user@example.com"
        result = get_permission_query_conditions(test_email, "Delivery Note")

        self.assertIn("`tabDelivery Note`.company IN", result)

    def test_purchase_receipt_filtered_by_company(self):
        """Purchase Receipt should be filtered by company field."""
        from pupa_franchise.api.permission import get_permission_query_conditions

        test_email = "test_franchise_user@example.com"
        result = get_permission_query_conditions(test_email, "Purchase Receipt")

        self.assertIn("`tabPurchase Receipt`.company IN", result)


class TestHasPermission(FrappeTestCase):
    """Tests for has_permission — per-document permission checks."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Reuse setup from above
        TestPermissionQueryConditions._ensure_test_companies()
        TestPermissionQueryConditions._ensure_test_user()

    def test_administrator_always_has_permission(self):
        """Administrator should always have permission."""
        from pupa_franchise.api.permission import has_permission

        # Create a mock doc-like object
        doc = frappe._dict({"doctype": "Sales Order", "company": "_Test Franchise B"})
        result = has_permission(doc, "read", "Administrator")
        self.assertTrue(result)

    def test_system_manager_always_has_permission(self):
        """System Manager role should always have permission."""
        from pupa_franchise.api.permission import has_permission

        admin_users = frappe.get_all("Has Role", filters={
            "role": "System Manager", "parenttype": "User"
        }, fields=["parent"], limit=1)

        if admin_users:
            doc = frappe._dict({"doctype": "Sales Order", "company": "_Test Franchise B"})
            result = has_permission(doc, "read", admin_users[0].parent)
            self.assertTrue(result)

    def test_user_can_access_own_company_doc(self):
        """User restricted to Company A should access Company A's documents."""
        from pupa_franchise.api.permission import has_permission

        test_email = "test_franchise_user@example.com"
        doc = frappe._dict({"doctype": "Sales Order", "company": "_Test Franchise A"})
        result = has_permission(doc, "read", test_email)
        self.assertTrue(result)

    def test_user_cannot_access_other_company_doc(self):
        """User restricted to Company A should NOT access Company B's documents."""
        from pupa_franchise.api.permission import has_permission

        test_email = "test_franchise_user@example.com"
        doc = frappe._dict({"doctype": "Sales Order", "company": "_Test Franchise B"})
        result = has_permission(doc, "read", test_email)
        self.assertFalse(result)

    def test_customer_permission_with_allowed_companies(self):
        """Customer doc with matching Allowed Company should be accessible."""
        from pupa_franchise.api.permission import has_permission

        test_email = "test_franchise_user@example.com"

        # Simulate Customer with allowed companies child table
        doc = frappe._dict({
            "doctype": "Customer",
            "custom_allowed_companies": [
                frappe._dict({"company": "_Test Franchise A"})
            ]
        })
        result = has_permission(doc, "read", test_email)
        self.assertTrue(result)

    def test_customer_permission_without_matching_company(self):
        """Customer doc without matching Allowed Company should be denied."""
        from pupa_franchise.api.permission import has_permission

        test_email = "test_franchise_user@example.com"

        doc = frappe._dict({
            "doctype": "Customer",
            "custom_allowed_companies": [
                frappe._dict({"company": "_Test Franchise B"})
            ]
        })
        result = has_permission(doc, "read", test_email)
        self.assertFalse(result)

    def test_customer_permission_empty_allowed_companies(self):
        """Customer doc with empty allowed companies list should be denied."""
        from pupa_franchise.api.permission import has_permission

        test_email = "test_franchise_user@example.com"

        doc = frappe._dict({
            "doctype": "Customer",
            "custom_allowed_companies": []
        })
        result = has_permission(doc, "read", test_email)
        self.assertFalse(result)

    def test_item_price_with_matching_company(self):
        """Item Price with matching custom_company should be accessible."""
        from pupa_franchise.api.permission import has_permission

        test_email = "test_franchise_user@example.com"

        doc = frappe._dict({
            "doctype": "Item Price",
            "custom_company": "_Test Franchise A"
        })
        result = has_permission(doc, "read", test_email)
        self.assertTrue(result)

    def test_item_price_with_wrong_company(self):
        """Item Price with different custom_company should be denied."""
        from pupa_franchise.api.permission import has_permission

        test_email = "test_franchise_user@example.com"

        doc = frappe._dict({
            "doctype": "Item Price",
            "custom_company": "_Test Franchise B"
        })
        result = has_permission(doc, "read", test_email)
        self.assertFalse(result)

    def test_item_price_with_blank_company_denied(self):
        """Item Price with blank custom_company should be denied for company users."""
        from pupa_franchise.api.permission import has_permission

        test_email = "test_franchise_user@example.com"

        doc = frappe._dict({
            "doctype": "Item Price",
            "custom_company": ""
        })
        result = has_permission(doc, "read", test_email)
        self.assertFalse(result)

    def test_item_price_with_none_company_denied(self):
        """Item Price with None custom_company should be denied."""
        from pupa_franchise.api.permission import has_permission

        test_email = "test_franchise_user@example.com"

        doc = frappe._dict({
            "doctype": "Item Price",
            "custom_company": None
        })
        result = has_permission(doc, "read", test_email)
        self.assertFalse(result)

    def test_bin_permission_checks_warehouse_company(self):
        """Bin permission should check the warehouse's company."""
        from pupa_franchise.api.permission import has_permission

        test_email = "test_franchise_user@example.com"

        # Find a warehouse belonging to _Test Franchise A
        warehouse = frappe.db.get_value("Warehouse",
            {"company": "_Test Franchise A"}, "name")

        if warehouse:
            doc = frappe._dict({
                "doctype": "Bin",
                "warehouse": warehouse,
            })
            result = has_permission(doc, "read", test_email)
            self.assertTrue(result)

    def test_bin_permission_denied_for_other_company_warehouse(self):
        """Bin for a different company's warehouse should be denied."""
        from pupa_franchise.api.permission import has_permission

        test_email = "test_franchise_user@example.com"

        # Find a warehouse belonging to _Test Franchise B
        warehouse = frappe.db.get_value("Warehouse",
            {"company": "_Test Franchise B"}, "name")

        if warehouse:
            doc = frappe._dict({
                "doctype": "Bin",
                "warehouse": warehouse,
            })
            result = has_permission(doc, "read", test_email)
            self.assertFalse(result)

    def test_user_without_company_restrictions_has_access(self):
        """User without any company User Permission should have full access."""
        from pupa_franchise.api.permission import has_permission

        no_restriction_email = "test_no_restriction@example.com"
        if not frappe.db.exists("User", no_restriction_email):
            frappe.get_doc({
                "doctype": "User",
                "email": no_restriction_email,
                "first_name": "No Restriction",
                "user_type": "System User",
                "send_welcome_email": 0,
                "roles": [{"role": "Stock User"}],
            }).insert(ignore_permissions=True)
            frappe.db.commit()

        doc = frappe._dict({"doctype": "Sales Order", "company": "_Test Franchise B"})
        result = has_permission(doc, "read", no_restriction_email)
        self.assertTrue(result)
