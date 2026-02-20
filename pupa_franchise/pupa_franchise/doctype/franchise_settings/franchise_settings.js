// Copyright (c) 2026, Tridots and contributors
// For license information, please see license.txt

frappe.ui.form.on("Franchise Settings", {
	refresh(frm) {
        frm.add_custom_button("Trigger", () => {
            frappe.call({
                method: "pupa_franchise.api.api_sync.get_api_settings",
                callback: function (r) {
                    if (r.message) {
                        console.log("Res", r.message)
                    }
                }
            })
        })
	},
});
