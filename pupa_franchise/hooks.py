app_name = "pupa_franchise"
app_title = "Pupa Franchise"
app_publisher = "Tridots"
app_description = "Pupa Franchise"
app_email = "britvasan@tridotstech.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "pupa_franchise",
# 		"logo": "/assets/pupa_franchise/logo.png",
# 		"title": "Pupa Franchise",
# 		"route": "/pupa_franchise",
# 		"has_permission": "pupa_franchise.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/pupa_franchise/css/pupa_franchise.css"
# app_include_js = "/assets/pupa_franchise/js/pupa_franchise.js"

# include js, css files in header of web template
# web_include_css = "/assets/pupa_franchise/css/pupa_franchise.css"
# web_include_js = "/assets/pupa_franchise/js/pupa_franchise.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "pupa_franchise/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "pupa_franchise/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "pupa_franchise.utils.jinja_methods",
# 	"filters": "pupa_franchise.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "pupa_franchise.install.before_install"
# after_install = "pupa_franchise.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "pupa_franchise.uninstall.before_uninstall"
# after_uninstall = "pupa_franchise.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "pupa_franchise.utils.before_app_install"
# after_app_install = "pupa_franchise.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "pupa_franchise.utils.before_app_uninstall"
# after_app_uninstall = "pupa_franchise.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "pupa_franchise.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

doc_events = {
    # "Supplier": {
    #     "after_insert": [
    #         "pupa_franchise.api.api_sync.create_franchise_supplier_to_pupa_customer"
    #     ]
    # },
    "Purchase Order": {
        "on_submit": [
            "pupa_franchise.api.api_sync.create_so_from_franchise_po"
        ]
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"pupa_franchise.tasks.all"
# 	],
# 	"daily": [
# 		"pupa_franchise.tasks.daily"
# 	],
# 	"hourly": [
# 		"pupa_franchise.tasks.hourly"
# 	],
# 	"weekly": [
# 		"pupa_franchise.tasks.weekly"
# 	],
# 	"monthly": [
# 		"pupa_franchise.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "pupa_franchise.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "pupa_franchise.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "pupa_franchise.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["pupa_franchise.utils.before_request"]
# after_request = ["pupa_franchise.utils.after_request"]

# Job Events
# ----------
# before_job = ["pupa_franchise.utils.before_job"]
# after_job = ["pupa_franchise.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"pupa_franchise.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

