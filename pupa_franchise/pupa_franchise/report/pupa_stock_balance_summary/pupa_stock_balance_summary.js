// Copyright (c) 2026, Tridots and contributors
// For license information, please see license.txt

function get_pupa_warehouses() {
	let warehouse_options = [""];
	frappe.call({
		method: "pupa_franchise.api.api_sync.get_pupa_warehouses",
		async: false,
		callback: function (r) {
			if (r && r.message && r.message.length) {
				warehouse_options = warehouse_options.concat(r.message);
			}
		}
	});
	return warehouse_options.join("\n");
}

frappe.query_reports["Pupa Stock Balance Summary"] = {
	filters: [
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Select",
			options: get_pupa_warehouses(),
			reqd: 1,
			on_change: function () {
				frappe.query_report.refresh();
			}
		}
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "actual_qty" && data && data.actual_qty > 0) {
			value = "<span style='color:green; font-weight:bold'>" + value + "</span>";
		}
		return value;
	}
};
