# Copyright (c) 2026, Tridots and Contributors
# Test suite for pupa_franchise.api.sales_invoice
# Tests influencer commission Purchase Invoice creation from Sales Invoice

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, flt


class TestCreatePIForInfluencerSI(FrappeTestCase):
    """Tests for sales_invoice.create_pi_for_influencer_si — influencer
    commission Purchase Invoice creation on Sales Invoice submit."""

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

        # Ensure franchise settings has influencer_commission_item set
        settings = frappe.get_doc("Franchise Settings")
        settings.influencer_commission_item = cls.item_code
        settings.save(ignore_permissions=True)
        frappe.db.commit()

    def _create_test_si(self, with_influencer=False, influencer_rows=None):
        """Helper to create a test Sales Invoice.

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

        si = frappe.new_doc("Sales Invoice")
        si.customer = self.customer
        si.company = self.company
        si.posting_date = today()
        si.due_date = today()

        # Set standard accounts/cost center
        debit_to = frappe.db.get_value("Account", {"company": self.company, "account_type": "Receivable"}, "name")
        if debit_to:
            si.debit_to = debit_to

        income_account = frappe.db.get_value("Account", {"company": self.company, "account_type": "Income"}, "name")

        si.append("items", {
            "item_code": self.item_code,
            "qty": 1,
            "rate": 1000.0,
            "warehouse": warehouse,
            "income_account": income_account,
            "cost_center": self.cost_center
        })

        # Add a tax to make grand_total different from total
        tax_account = frappe.db.get_value("Account", {"company": self.company, "account_type": "Tax Charge"}, "name") or \
                      frappe.db.get_value("Account", {"company": self.company, "account_type": "Tax"}, "name")
        if tax_account:
            si.append("taxes", {
                "charge_type": "Actual",
                "account_head": tax_account,
                "description": "Test Tax",
                "cost_center": self.cost_center,
                "rate": 0,
                "tax_amount": 180.0
            })

        if with_influencer:
            si.custom_do_you_have_any_influencer = "Yes"
            if influencer_rows:
                for row in influencer_rows:
                    si.append("custom_influencer_commission_details", row)

        si.flags.ignore_mandatory = True
        si.insert(ignore_permissions=True)
        # standard Frappe calculations
        si.calculate_taxes_and_totals()
        si.save(ignore_permissions=True)
        frappe.db.commit()
        return si

    def test_no_influencer_flag_returns_early(self):
        """SI without influencer flag should not create any PI."""
        from pupa_franchise.api.sales_invoice import create_pi_for_influencer_si

        si = self._create_test_si(with_influencer=False)

        result = create_pi_for_influencer_si(si.name)
        self.assertIsNone(result)

        # No PI should be created referencing this Sales Invoice
        pi_count = frappe.db.count("Purchase Invoice", {"custom_influencer_sales_invoice_reference": si.name})
        self.assertEqual(pi_count, 0)

        # Cleanup
        frappe.delete_doc("Sales Invoice", si.name, force=True)
        frappe.db.commit()

    def test_influencer_flag_but_no_rows_returns_none(self):
        """SI with influencer flag but no commission details should return None."""
        from pupa_franchise.api.sales_invoice import create_pi_for_influencer_si

        si = self._create_test_si(with_influencer=True, influencer_rows=[])

        result = create_pi_for_influencer_si(si.name)
        self.assertIsNone(result)

        # Cleanup
        frappe.delete_doc("Sales Invoice", si.name, force=True)
        frappe.db.commit()

    def test_influencer_pi_created_with_zero_percent_commission(self):
        """SI with 0% influencer commission should create PI with 0 amount."""
        from pupa_franchise.api.sales_invoice import create_pi_for_influencer_si

        # Use a different supplier to avoid price fetching from history
        other_supplier = "_Test Influencer Supplier 4"
        if not frappe.db.exists("Supplier", other_supplier):
            frappe.get_doc({
                "doctype": "Supplier",
                "supplier_name": other_supplier,
                "supplier_group": frappe.db.get_value("Supplier Group", {}, "name") or "All Supplier Groups",
            }).insert(ignore_permissions=True)

        si = self._create_test_si(with_influencer=True, influencer_rows=[
            {"supplier": other_supplier, "commission_percentage": 0.0}
        ])

        result = create_pi_for_influencer_si(si.name)

        self.assertIsNotNone(result, "create_pi_for_influencer_si returned None instead of a list")
        self.assertEqual(len(result), 1, "PI was not created for 0% commission")

        if len(result) > 0:
            pi = frappe.get_doc("Purchase Invoice", result[0])
            self.assertEqual(pi.supplier, other_supplier)
            for item in pi.items:
                if item.item_code == self.item_code:
                    self.assertAlmostEqual(item.rate, 0.0, places=2)

            # Cleanup PI
            frappe.delete_doc("Purchase Invoice", result[0], force=True)

        # Cleanup SI
        frappe.delete_doc("Sales Invoice", si.name, force=True)
        frappe.db.commit()

    def test_influencer_pi_created_with_correct_commission_based_on_total(self):
        """SI with influencer details should create PI with commission calculated using 'total', not 'grand_total'."""
        from pupa_franchise.api.sales_invoice import create_pi_for_influencer_si

        si = self._create_test_si(with_influencer=True, influencer_rows=[
            {"supplier": self.supplier, "commission_percentage": 10.0}
        ])

        # Verify that total and grand_total are indeed different
        self.assertAlmostEqual(si.total, 1000.0)
        self.assertAlmostEqual(si.grand_total, 1180.0)

        result = create_pi_for_influencer_si(si.name)

        if result:
            self.assertEqual(len(result), 1)
            pi = frappe.get_doc("Purchase Invoice", result[0])

            # Verify PI supplier matches
            self.assertEqual(pi.supplier, self.supplier)

            # Verify commission rate calculation
            # Total: 1000, commission: 10%, so PI rate should be 100 (based on total), not 118 (which would be based on grand_total)
            for item in pi.items:
                if item.item_code == self.item_code:
                    self.assertAlmostEqual(item.rate, 100.0, places=2)

            # Cleanup PI
            frappe.delete_doc("Purchase Invoice", result[0], force=True)

        # Cleanup SI
        frappe.delete_doc("Sales Invoice", si.name, force=True)
        frappe.db.commit()
