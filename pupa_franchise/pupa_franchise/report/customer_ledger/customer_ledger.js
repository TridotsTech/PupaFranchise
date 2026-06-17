// Copyright (c) 2025, Thirvusoft and contributors
// For license information, please see license.txt

frappe.query_reports["Customer Ledger"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
			on_change: async function () {
				let company = frappe.query_report.get_filter_value("company");
				if (!company) {
					frappe.query_report.set_filter_value("company_address_line1", "");
					frappe.query_report.set_filter_value("company_address_line2", "");
					frappe.query_report.set_filter_value("company_city", "");
					frappe.query_report.set_filter_value("company_pincode", "");
					frappe.query_report.set_filter_value("gstin", "");
					frappe.query_report.refresh();
					return;
				}
				frappe.db.get_value("Company", company, "gstin", (r) => {
					if (r && r.gstin) {
						frappe.query_report.set_filter_value("gstin", r.gstin);
					} else {
						frappe.query_report.set_filter_value("gstin", "");
					}
					frappe.query_report.refresh();
				});
				frappe.call({
					method: "pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger.company_address",
					args: { company },
					callback: function (r) {
						if (r.message) {
							frappe.query_report.set_filter_value("company_address_line1", r.message[0] || "");
							frappe.query_report.set_filter_value("company_address_line2", r.message[1] || "");
							frappe.query_report.set_filter_value("company_city", r.message[2] || "");
							frappe.query_report.set_filter_value("company_pincode", r.message[3] || "");
							frappe.query_report.refresh();
						}
					}
				});
				
			},
		},		
		{
			fieldname: "customer_group",
			label: __("Customer Group"),
			fieldtype: "Link",
			options: "Customer Group",
			get_query: function () {
				return {
					filters: {
						"is_group":0
					},
				};
			},
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
			on_change: function () {
				let customer = frappe.query_report.get_filter_value("customer");
				frappe.query_report.set_filter_value("party_address_line1", "");
				frappe.query_report.set_filter_value("party_address_line2", "");
				frappe.query_report.set_filter_value("party_city", "");
				frappe.query_report.set_filter_value("party_pincode", "");
				frappe.query_report.set_filter_value("party_gstin", "");
				frappe.query_report.refresh();
				if (customer) {
					frappe.call({
						method: "pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger.party_address",
						args: {
							party_type: "Customer",
							party: customer
						},
						callback: function (r) {
							if (r.message) {
								frappe.query_report.set_filter_value("party_address_line1", r.message[0] || "");
								frappe.query_report.set_filter_value("party_address_line2", r.message[1] || "");
								frappe.query_report.set_filter_value("party_city", r.message[2] || "");
								frappe.query_report.set_filter_value("party_pincode", r.message[3] || "");
								frappe.query_report.set_filter_value("party_gstin", r.message[4] || "");
								frappe.query_report.refresh();
							}
						}
					});
				}
			}
		},		
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
		},
		{
			fieldname: "voucher_type",
			label: __("Voucher Type"),
			fieldtype: "Data",
		},
		{
			fieldname: "voucher_no",
			label: __("Voucher No"),
			fieldtype: "Data"
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch"
		},
		{
			fieldname: "company_address_line1",
			label: __("Address Line1"),
			fieldtype: "Data",
			hidden: 1,
		},
		{
			fieldname: "company_address_line2",
			label: __("Address Line2"),
			fieldtype: "Data",
			hidden: 1,
		},
		{
			fieldname: "company_city",
			label: __("Party City"),
			fieldtype: "Data",
			hidden: 1,
		},
		{
			fieldname: "company_pincode",
			label: __("Party Pincode"),
			fieldtype: "Data",
			hidden: 1,
		},
		{
			fieldname: "gstin",
			label: __("GSTIN"),
			fieldtype: "Data",
			hidden: 1,
		},
		{
			fieldname: "party_address_line1",
			label: __("Address Line1"),
			fieldtype: "Data",
			hidden: 1,
		},
		{
			fieldname: "party_address_line2",
			label: __("Address Line2"),
			fieldtype: "Data",
			hidden: 1,
		},
		{
			fieldname: "party_city",
			label: __("Party City"),
			fieldtype: "Data",
			hidden: 1,
		},
		{
			fieldname: "party_pincode",
			label: __("Party Pincode"),
			fieldtype: "Data",
			hidden: 1,
		},
		{
			fieldname: "party_gstin",
			label: __("Party Gstin"),
			fieldtype: "Data",
			hidden: 1,
		},
	],
	onload: function (report) {
		let company = frappe.query_report.get_filter_value("company");
		if (!company) {
			frappe.query_report.set_filter_value("company_address_line1", "");
			frappe.query_report.set_filter_value("company_address_line2", "");
			frappe.query_report.set_filter_value("company_city", "");
			frappe.query_report.set_filter_value("company_pincode", "");
			frappe.query_report.set_filter_value("gstin", "");
			frappe.query_report.refresh();
			return;
		}
		frappe.db.get_value("Company", company, "gstin", (r) => {
			if (r && r.gstin) {
				frappe.query_report.set_filter_value("gstin", r.gstin);
			} else {
				frappe.query_report.set_filter_value("gstin", "");
			}
			frappe.query_report.refresh();
		});
		frappe.call({
			method: "pupa_franchise.pupa_franchise.report.customer_ledger.customer_ledger.company_address",
			args: { company },
			callback: function (r) {
				if (r.message) {
					frappe.query_report.set_filter_value("company_address_line1", r.message[0] || "");
					frappe.query_report.set_filter_value("company_address_line2", r.message[1] || "");
					frappe.query_report.set_filter_value("company_city", r.message[2] || "");
					frappe.query_report.set_filter_value("company_pincode", r.message[3] || "");
					frappe.query_report.refresh();
				}
			}
		});
	  },
	formatter: function (value, row, column, data, default_formatter) {
		
		if (column.fieldname == "against" && (data.against == 'Opening Balance' || data.against == 'Closing Balance')) {
			value = __(default_formatter(value, row, column, data));
			value = $(`<b>${data.against}</b>`);
			var $value = $(value);
			value = $value.wrap("<p></p>").parent().html();
		} else {
			value = __(default_formatter(value, row, column, data));
		}
		return value
	}
};
