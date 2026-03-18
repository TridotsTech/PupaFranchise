# Copyright (c) 2026, Tridots and Contributors
# Test suite for pupa_franchise.api.api_sync
# Tests item/company/branch creation, purchase receipt/invoice creation,
# pricing rule sync, and draft PO update logic

import frappe
import json
from frappe.tests.utils import FrappeTestCase


def _ensure_franchise_settings():
    """Ensure Franchise Settings has minimum required fields for testing."""
    settings = frappe.get_single("Franchise Settings")
    if not settings.default_supplier:
        # Try to find any existing supplier
        supplier = frappe.db.get_value("Supplier", {}, "name")
        if supplier:
            settings.default_supplier = supplier
            settings.save(ignore_permissions=True)
            frappe.db.commit()


class TestCreateItem(FrappeTestCase):
    """Tests for api_sync.create_item — creating Items from HQ payload."""

    def test_create_item_success(self):
        """Creating an item with valid data should succeed."""
        from pupa_franchise.api.api_sync import create_item

        item_code = "_Test Franchise Item 001"
        # Clean up first
        if frappe.db.exists("Item", item_code):
            frappe.delete_doc("Item", item_code, force=True)
            frappe.db.commit()

        result = create_item(
            item_code=item_code,
            item_name="Test Franchise Item 001",
            item_group="All Item Groups",
            stock_uom="Nos",
        )
        self.assertEqual(result, item_code)
        self.assertTrue(frappe.db.exists("Item", item_code))

        # Cleanup
        frappe.delete_doc("Item", item_code, force=True)
        frappe.db.commit()

    def test_create_item_duplicate_skipped(self):
        """Creating an item that already exists should return 'skipped'."""
        from pupa_franchise.api.api_sync import create_item

        item_code = "_Test Franchise Item Dup"
        if not frappe.db.exists("Item", item_code):
            frappe.get_doc({
                "doctype": "Item",
                "item_code": item_code,
                "item_name": item_code,
                "item_group": "All Item Groups",
                "stock_uom": "Nos",
            }).insert(ignore_permissions=True)
            frappe.db.commit()

        result = create_item(
            item_code=item_code,
            item_name=item_code,
            item_group="All Item Groups",
            stock_uom="Nos",
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "skipped")

        # Cleanup
        frappe.delete_doc("Item", item_code, force=True)
        frappe.db.commit()

    def test_create_item_without_code_throws(self):
        """Creating an item without item_code should throw an error."""
        from pupa_franchise.api.api_sync import create_item

        with self.assertRaises(frappe.exceptions.ValidationError):
            create_item(item_code=None)

    def test_create_item_invalid_item_group_skipped(self):
        """Creating an item with non-existent item group should return 'skipped'."""
        from pupa_franchise.api.api_sync import create_item

        result = create_item(
            item_code="_Test Franchise Item Bad Group",
            item_name="Bad Group Item",
            item_group="Non Existent Group XYZ",
            stock_uom="Nos",
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "skipped")


class TestCreateItemGroup(FrappeTestCase):
    """Tests for api_sync.create_item_group."""

    def test_create_item_group_franchise(self):
        """Creating franchise item group (franchise_group=1) should succeed."""
        from pupa_franchise.api.api_sync import create_item_group

        group_name = "_Test Franchise IG"
        if frappe.db.exists("Item Group", group_name):
            frappe.delete_doc("Item Group", group_name, force=True)
            frappe.db.commit()

        result = create_item_group(
            item_group_name=group_name,
            parent_item_group="All Item Groups",
            is_group=0,
            franchise_group=1,
        )
        self.assertEqual(result, group_name)
        self.assertTrue(frappe.db.exists("Item Group", group_name))

        # Cleanup
        frappe.delete_doc("Item Group", group_name, force=True)
        frappe.db.commit()

    def test_create_item_group_non_franchise_skipped(self):
        """Non-franchise item group (franchise_group=0) should be skipped."""
        from pupa_franchise.api.api_sync import create_item_group

        result = create_item_group(
            item_group_name="_Test Non Franchise IG",
            parent_item_group="All Item Groups",
            is_group=0,
            franchise_group=0,
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "skipped")

    def test_create_item_group_duplicate_skipped(self):
        """Duplicate franchise item group should be skipped."""
        from pupa_franchise.api.api_sync import create_item_group

        # All Item Groups always exists
        result = create_item_group(
            item_group_name="All Item Groups",
            parent_item_group="",
            is_group=1,
            franchise_group=1,
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "skipped")

    def test_create_item_group_no_name_throws(self):
        """Missing item_group_name should throw."""
        from pupa_franchise.api.api_sync import create_item_group

        with self.assertRaises(frappe.exceptions.ValidationError):
            create_item_group(item_group_name=None)


class TestCreateBranch(FrappeTestCase):
    """Tests for api_sync.create_branch."""

    def test_create_branch_success(self):
        """Creating a branch should succeed."""
        from pupa_franchise.api.api_sync import create_branch

        branch_name = "_Test Franchise Branch"
        if frappe.db.exists("Branch", branch_name):
            frappe.delete_doc("Branch", branch_name, force=True)
            frappe.db.commit()

        result = create_branch(branch_name=branch_name)
        self.assertEqual(result, branch_name)
        self.assertTrue(frappe.db.exists("Branch", branch_name))

        # Cleanup
        frappe.delete_doc("Branch", branch_name, force=True)
        frappe.db.commit()

    def test_create_branch_duplicate_returns_none(self):
        """Creating a duplicate branch should return None."""
        from pupa_franchise.api.api_sync import create_branch

        branch_name = "_Test Franchise Branch Dup"
        if not frappe.db.exists("Branch", branch_name):
            frappe.get_doc({
                "doctype": "Branch", "branch": branch_name
            }).insert(ignore_permissions=True)
            frappe.db.commit()

        result = create_branch(branch_name=branch_name)
        self.assertIsNone(result)

        # Cleanup
        frappe.delete_doc("Branch", branch_name, force=True)
        frappe.db.commit()

    def test_create_branch_no_name_returns_none(self):
        """Missing branch_name should return None."""
        from pupa_franchise.api.api_sync import create_branch

        result = create_branch(branch_name=None)
        self.assertIsNone(result)


class TestCreateCompany(FrappeTestCase):
    """Tests for api_sync.create_company."""

    def test_create_company_success(self):
        """Creating a company should use system defaults."""
        from pupa_franchise.api.api_sync import create_company

        company_name = "_Test Franchise Co New"
        branch_name = "_Test Branch for Co"

        # Ensure branch exists
        if not frappe.db.exists("Branch", branch_name):
            frappe.get_doc({
                "doctype": "Branch", "branch": branch_name
            }).insert(ignore_permissions=True)
            frappe.db.commit()

        if frappe.db.exists("Company", company_name):
            frappe.delete_doc("Company", company_name, force=True)
            frappe.db.commit()

        result = create_company(company_name=company_name, branch_name=branch_name)
        self.assertEqual(result, company_name)
        self.assertTrue(frappe.db.exists("Company", company_name))

        # Verify system defaults used
        company = frappe.get_doc("Company", company_name)
        system_settings = frappe.get_single("System Settings")
        self.assertEqual(company.default_currency, system_settings.currency)
        self.assertEqual(company.custom_branch, branch_name)

        # Cleanup
        frappe.delete_doc("Company", company_name, force=True)
        if frappe.db.exists("Branch", branch_name):
            frappe.delete_doc("Branch", branch_name, force=True)
        frappe.db.commit()

    def test_create_company_no_name_returns_none(self):
        """Missing company_name should return None."""
        from pupa_franchise.api.api_sync import create_company

        result = create_company(company_name=None, branch_name="Some Branch")
        self.assertIsNone(result)

    def test_create_company_no_branch_returns_none(self):
        """Missing branch_name should return None."""
        from pupa_franchise.api.api_sync import create_company

        result = create_company(company_name="Some Company", branch_name=None)
        self.assertIsNone(result)


class TestCreatePurchaseReceipt(FrappeTestCase):
    """Tests for api_sync.create_purchase_receipt."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _ensure_franchise_settings()

    def test_create_purchase_receipt_success(self):
        """Creating a purchase receipt with valid items should succeed."""
        from pupa_franchise.api.api_sync import create_purchase_receipt

        company = frappe.db.get_value("Company", {}, "name")
        if not company:
            self.skipTest("No company found for testing")

        supplier = frappe.db.get_single_value("Franchise Settings", "default_supplier")
        if not supplier:
            self.skipTest("No default supplier in Franchise Settings")

        item = frappe.db.get_value("Item", {}, "name")
        if not item:
            self.skipTest("No item found for testing")

        items = json.dumps([{
            "item_code": item,
            "item_name": item,
            "qty": 5,
            "uom": "Nos",
            "rate": 100,
            "amount": 500,
        }])

        result = create_purchase_receipt(
            supplier=supplier,
            company=company,
            posting_date="2026-03-17",
            custom_sales_invoice_id="TEST-SI-001",
            items=items,
        )

        self.assertIn("message", result)
        pr_name = result["message"]
        self.assertTrue(frappe.db.exists("Purchase Receipt", pr_name))

        # Verify it's a draft
        pr = frappe.get_doc("Purchase Receipt", pr_name)
        self.assertEqual(pr.docstatus, 0)

        # Cleanup
        frappe.delete_doc("Purchase Receipt", pr_name, force=True)
        frappe.db.commit()

    def test_create_purchase_receipt_no_supplier_throws(self):
        """Missing supplier should throw."""
        from pupa_franchise.api.api_sync import create_purchase_receipt

        with self.assertRaises(Exception):
            create_purchase_receipt(
                supplier=None,
                company="Test",
                posting_date="2026-03-17",
                items='[{"item_code": "X", "qty": 1}]',
            )

    def test_create_purchase_receipt_no_items_throws(self):
        """Missing items should throw."""
        from pupa_franchise.api.api_sync import create_purchase_receipt

        with self.assertRaises(Exception):
            create_purchase_receipt(
                supplier="Test Supplier",
                company="Test",
                posting_date="2026-03-17",
                items=None,
            )


class TestCreatePurchaseInvoice(FrappeTestCase):
    """Tests for api_sync.create_purchase_invoice."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _ensure_franchise_settings()

    def test_create_purchase_invoice_success(self):
        """Creating a purchase invoice with valid items should succeed."""
        from pupa_franchise.api.api_sync import create_purchase_invoice

        company = frappe.db.get_value("Company", {}, "name")
        if not company:
            self.skipTest("No company found for testing")

        supplier = frappe.db.get_single_value("Franchise Settings", "default_supplier")
        if not supplier:
            self.skipTest("No default supplier in Franchise Settings")

        item = frappe.db.get_value("Item", {}, "name")
        if not item:
            self.skipTest("No item found for testing")

        items = json.dumps([{
            "item_code": item,
            "item_name": item,
            "qty": 2,
            "uom": "Nos",
            "rate": 200,
            "amount": 400,
        }])

        result = create_purchase_invoice(
            company=company,
            posting_date="2026-03-17",
            due_date="2026-04-17",
            custom_sales_invoice_id="TEST-SI-002",
            items=items,
        )

        self.assertIn("message", result)
        pi_name = result["message"]
        self.assertTrue(frappe.db.exists("Purchase Invoice", pi_name))

        # Verify it's a draft
        pi = frappe.get_doc("Purchase Invoice", pi_name)
        self.assertEqual(pi.docstatus, 0)
        self.assertEqual(pi.update_stock, 1)

        # Cleanup
        frappe.delete_doc("Purchase Invoice", pi_name, force=True)
        frappe.db.commit()

    def test_create_purchase_invoice_no_items_throws(self):
        """Missing items should throw."""
        from pupa_franchise.api.api_sync import create_purchase_invoice

        with self.assertRaises(Exception):
            create_purchase_invoice(
                company="Test",
                posting_date="2026-03-17",
                items=None,
            )


class TestApprovePurchaseInvoice(FrappeTestCase):
    """Tests for api_sync.approve_purchase_invoice."""

    def test_approve_no_name_throws(self):
        """Missing purchase_invoice_name should throw."""
        from pupa_franchise.api.api_sync import approve_purchase_invoice

        with self.assertRaises(Exception):
            approve_purchase_invoice(purchase_invoice_name=None)


class TestCreateOrUpdatePricingRule(FrappeTestCase):
    """Tests for api_sync.create_or_update_pricing_rule."""

    def test_create_pricing_rule_success(self):
        """Creating a Pricing Rule from HQ payload should succeed."""
        from pupa_franchise.api.api_sync import create_or_update_pricing_rule

        ho_id = "_TEST_PR_HO_001"
        # Clean up
        existing = frappe.db.get_value("Pricing Rule",
            {"custom_ho_pricing_rule_id": ho_id}, "name")
        if existing:
            frappe.delete_doc("Pricing Rule", existing, force=True)
            frappe.db.commit()

        result = create_or_update_pricing_rule(
            custom_ho_pricing_rule_id=ho_id,
            title="Test Franchise Pricing Rule",
            apply_on="Item Code",
            price_or_product_discount="Price",
            selling=1,
            buying=0,
            rate_or_discount="Discount Percentage",
            discount_percentage=10,
            currency="INR",
            items=json.dumps([]),
        )

        self.assertIn("name", result)
        self.assertIn("created", result["message"])

        # Verify created
        self.assertTrue(frappe.db.exists("Pricing Rule", result["name"]))

        # Cleanup
        frappe.delete_doc("Pricing Rule", result["name"], force=True)
        frappe.db.commit()

    def test_update_pricing_rule(self):
        """Updating an existing Pricing Rule should not create a duplicate."""
        from pupa_franchise.api.api_sync import create_or_update_pricing_rule

        ho_id = "_TEST_PR_HO_002"
        # Clean up
        existing = frappe.db.get_value("Pricing Rule",
            {"custom_ho_pricing_rule_id": ho_id}, "name")
        if existing:
            frappe.delete_doc("Pricing Rule", existing, force=True)
            frappe.db.commit()

        # Create first
        result1 = create_or_update_pricing_rule(
            custom_ho_pricing_rule_id=ho_id,
            title="Test PR Original",
            apply_on="Item Code",
            price_or_product_discount="Price",
            selling=1,
            rate_or_discount="Discount Percentage",
            discount_percentage=5,
            currency="INR",
            items=json.dumps([]),
        )

        # Update
        result2 = create_or_update_pricing_rule(
            custom_ho_pricing_rule_id=ho_id,
            title="Test PR Updated",
            apply_on="Item Code",
            price_or_product_discount="Price",
            selling=1,
            rate_or_discount="Discount Percentage",
            discount_percentage=15,
            currency="INR",
            items=json.dumps([]),
        )

        self.assertIn("updated", result2["message"])
        # Same name should be reused
        self.assertEqual(result1["name"], result2["name"])

        # Verify discount updated
        pr = frappe.get_doc("Pricing Rule", result2["name"])
        self.assertEqual(pr.discount_percentage, 15)

        # Cleanup
        frappe.delete_doc("Pricing Rule", result2["name"], force=True)
        frappe.db.commit()

    def test_create_pricing_rule_no_ho_id_throws(self):
        """Missing ho_pricing_rule_id should throw."""
        from pupa_franchise.api.api_sync import create_or_update_pricing_rule

        with self.assertRaises(Exception):
            create_or_update_pricing_rule(
                custom_ho_pricing_rule_id=None,
                title="Test",
            )
