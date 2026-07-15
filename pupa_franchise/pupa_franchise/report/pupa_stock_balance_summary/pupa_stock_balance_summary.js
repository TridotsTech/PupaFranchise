// Copyright (c) 2026, Tridots and contributors
// For license information, please see license.txt

frappe.query_reports["Pupa Stock Balance Summary"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			on_change: function () {
				let company = frappe.query_report.get_filter_value("company");
				let warehouse_filter = frappe.query_report.get_filter("warehouse");
				if (!warehouse_filter) return;

				if (company) {
					frappe.call({
						method: "pupa_franchise.api.api_sync.get_pupa_warehouses",
						args: { company: company },
						callback: function (r) {
							if (r && r.message && r.message.length) {
								let warehouse_options = [""].concat(r.message);
								warehouse_filter.df.options = warehouse_options.join("\n");
								warehouse_filter.refresh();
								frappe.query_report.set_filter_value("warehouse", "");
							} else {
								warehouse_filter.df.options = "\n";
								warehouse_filter.refresh();
								frappe.query_report.set_filter_value("warehouse", "");
								frappe.throw(__("No warehouse is mapped against this company in Pupa Settings"));
							}
						}
					});
				} else {
					warehouse_filter.df.options = "\n";
					warehouse_filter.refresh();
					frappe.query_report.set_filter_value("warehouse", "");
				}
			}
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Select",
			options: "",
			reqd: 1,
			on_change: function () {
				frappe.query_report.refresh();
			}
		}
	],

	onload: function (report) {
		let company = frappe.query_report.get_filter_value("company");
		if (company) {
			frappe.query_report.get_filter("company").on_change();
		}
	},

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "actual_qty" && data && data.actual_qty > 0) {
			value = "<span style='color:green; font-weight:bold'>" + value + "</span>";
		}
		return value;
	}
};
