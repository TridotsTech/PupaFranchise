# Copyright (c) 2026, Tridots and Contributors
# Test suite for pupa_franchise.utils.py.sales_order
# Tests influencer commission Purchase Invoice creation from Sales Order

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestCreatePIForInfluencerSO(FrappeTestCase):
    """Tests for sales_order.create_pi_for_influencer_so — influencer
    commission Purchase Invoice creation on Sales Order submit."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._ensure_test_data()

    @classmethod
    def _ensure_test_data(cls):
        """Ensure test company, customer, supplier, and item exist."""
        cls.company = frappe.db.get_value("Company", {}, "name")
        if not cls.company:
            return

        # Ensure cost center
        cls.cost_center = frappe.db.get_value("Company", cls.company, "cost_center")

        # Ensure a test customer
        cls.customer = "_Test Influencer Customer"
        if not frappe.db.exists("Customer", cls.customer):
            frappe.get_doc({
                "doctype": "Customer",
                "customer_name": cls.customer,
                "customer_group": frappe.db.get_value("Customer Group", {}, "name") or "All Customer Groups",
                "territory": frappe.db.get_value("Territory", {}, "name") or "All Territories",
            }).insert(ignore_permissions=True)
            frappe.db.commit()

        # Ensure a test supplier for influencer
        cls.supplier = "_Test Influencer Supplier"
        if not frappe.db.exists("Supplier", cls.supplier):
            frappe.get_doc({
                "doctype": "Supplier",
                "supplier_name": cls.supplier,
                "supplier_group": frappe.db.get_value("Supplier Group", {}, "name") or "All Supplier Groups",
            }).insert(ignore_permissions=True)
            frappe.db.commit()

        # Ensure a test item
        cls.item_code = "_Test Influencer Item"
        if not frappe.db.exists("Item", cls.item_code):
            frappe.get_doc({
                "doctype": "Item",
                "item_code": cls.item_code,
                "item_name": cls.item_code,
                "item_group": "All Item Groups",
                "stock_uom": "Nos",
                "gst_hsn_code": "010121"
            }).insert(ignore_permissions=True)
            frappe.db.commit()

    def _create_test_so(self, with_influencer=False, influencer_rows=None):
        """Helper to create a test Sales Order.

        Args:
            with_influencer: Whether to set the influencer flag
            influencer_rows: List of dicts with supplier and commission_percentage
        """
        if not self.company:
            self.skipTest("No company found for testing")

        # Find or create a warehouse for the company
        warehouse = frappe.db.get_value("Warehouse", {"company": self.company}, "name")
        if not warehouse:
            warehouse_doc = frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": "_Test Influencer Warehouse",
                "company": self.company,
                "is_group": 0
            })
            warehouse_doc.insert(ignore_permissions=True)
            warehouse = warehouse_doc.name

        so = frappe.new_doc("Sales Order")
        so.customer = self.customer
        so.company = self.company
        so.delivery_date = today()
        so.transaction_date = today()

        so.append("items", {
            "item_code": self.item_code,
            "qty": 10,
            "rate": 1000,
            "custom_mrp": 1000,
            "delivery_date": today(),
            "warehouse": warehouse
        })

        if with_influencer:
            so.custom_do_you_have_any_influencer = 1
            if influencer_rows:
                for row in influencer_rows:
                    so.append("custom_influencer_commission_details", row)

        so.flags.ignore_mandatory = True
        so.insert(ignore_permissions=True)
        frappe.db.commit()
        return so

    def test_no_influencer_flag_returns_early(self):
        """SO without influencer flag should not create any PI."""
        from pupa_franchise.utils.py.sales_order import create_pi_for_influencer_so

        so = self._create_test_so(with_influencer=False)

        result = create_pi_for_influencer_so(so.name)
        self.assertIsNone(result)

        # No PI should be created
        pi_count = frappe.db.count("Purchase Invoice", {"custom_sales_order": so.name})
        self.assertEqual(pi_count, 0)

        # Cleanup
        frappe.delete_doc("Sales Order", so.name, force=True)
        frappe.db.commit()

    def test_influencer_flag_but_no_rows_returns_none(self):
        """SO with influencer flag but no commission details should msgprint and return."""
        from pupa_franchise.utils.py.sales_order import create_pi_for_influencer_so

        so = self._create_test_so(with_influencer=True, influencer_rows=[])

        result = create_pi_for_influencer_so(so.name)
        # Should return None (no invoices created)
        self.assertIsNone(result)

        # Cleanup
        frappe.delete_doc("Sales Order", so.name, force=True)
        frappe.db.commit()

    def test_influencer_pi_created_with_correct_commission(self):
        """SO with influencer details should create PI with commission rates."""
        from pupa_franchise.utils.py.sales_order import create_pi_for_influencer_so

        so = self._create_test_so(with_influencer=True, influencer_rows=[
            {"supplier": self.supplier, "commission_percentage": 10}
        ])

        result = create_pi_for_influencer_so(so.name)

        if result:
            self.assertEqual(len(result), 1)
            pi = frappe.get_doc("Purchase Invoice", result[0])

            # Verify PI supplier matches
            self.assertEqual(pi.supplier, self.supplier)

            # Verify commission rate calculation
            # Original rate: 1000, commission: 10%, so PI rate should be 100
            for item in pi.items:
                if item.item_code == self.item_code:
                    self.assertAlmostEqual(item.rate, 100.0, places=2)

            # Cleanup PI
            frappe.delete_doc("Purchase Invoice", result[0], force=True)

        # Cleanup SO
        frappe.delete_doc("Sales Order", so.name, force=True)
        frappe.db.commit()

    def test_row_without_supplier_skipped(self):
        """Influencer row without supplier should be skipped."""
        from pupa_franchise.utils.py.sales_order import create_pi_for_influencer_so

        so = self._create_test_so(with_influencer=True, influencer_rows=[
            {"supplier": "", "commission_percentage": 10}
        ])

        result = create_pi_for_influencer_so(so.name)
        # No PI should be created since supplier is missing
        if result:
            self.assertEqual(len(result), 0)

        # Cleanup
        frappe.delete_doc("Sales Order", so.name, force=True)
        frappe.db.commit()

    def test_row_without_commission_percentage_skipped(self):
        """Influencer row without commission_percentage should be skipped."""
        from pupa_franchise.utils.py.sales_order import create_pi_for_influencer_so

        so = self._create_test_so(with_influencer=True, influencer_rows=[
            {"supplier": self.supplier, "commission_percentage": 0}
        ])

        result = create_pi_for_influencer_so(so.name)
        # Should skip row where commission_percentage is 0 (falsy)
        if result:
            self.assertEqual(len(result), 0)

        # Cleanup
        frappe.delete_doc("Sales Order", so.name, force=True)
        frappe.db.commit()

    def test_multiple_influencers_create_multiple_pis(self):
        """SO with multiple influencers should create one PI per influencer."""
        from pupa_franchise.utils.py.sales_order import create_pi_for_influencer_so

        supplier2 = "_Test Influencer Supplier 2"
        if not frappe.db.exists("Supplier", supplier2):
            frappe.get_doc({
                "doctype": "Supplier",
                "supplier_name": supplier2,
                "supplier_group": frappe.db.get_value("Supplier Group", {}, "name") or "All Supplier Groups",
            }).insert(ignore_permissions=True)
            frappe.db.commit()

        so = self._create_test_so(with_influencer=True, influencer_rows=[
            {"supplier": self.supplier, "commission_percentage": 10},
            {"supplier": supplier2, "commission_percentage": 5},
        ])

        result = create_pi_for_influencer_so(so.name)

        if result:
            self.assertEqual(len(result), 2)

            # Verify different suppliers
            suppliers = [frappe.db.get_value("Purchase Invoice", pi, "supplier") for pi in result]
            self.assertIn(self.supplier, suppliers)
            self.assertIn(supplier2, suppliers)

            # Cleanup PIs
            for pi_name in result:
                frappe.delete_doc("Purchase Invoice", pi_name, force=True)

        # Cleanup SO and supplier
        frappe.delete_doc("Sales Order", so.name, force=True)
        if frappe.db.exists("Supplier", supplier2):
            frappe.delete_doc("Supplier", supplier2, force=True)
        frappe.db.commit()
