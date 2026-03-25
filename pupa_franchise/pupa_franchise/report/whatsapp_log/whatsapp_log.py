# Copyright (c) 2025, Thirvusoft and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns, data = [], []
	columns = [
		{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 120},
		{"label": "Status", "fieldname": "status", "fieldtype": "Select", "width": 100},
		{"label": "Reference Doctype", "fieldname": "reference_doctype", "fieldtype": "Link", "options": "DocType", "width": 150},
		{"label": "Reference Docname", "fieldname": "reference_docname", "fieldtype": "Dynamic Link", "options": "reference_doctype", "width": 150},
		{"label": "Party", "fieldname": "party", "fieldtype": "Data", "width": 150},
		{"label": "Mobile Number", "fieldname": "mobile_number", "fieldtype": "Data", "width": 120},
		{"label": "Message", "fieldname": "message", "fieldtype": "Small Text", "width": 300},
	]
	
	data = frappe.get_all("Whatsapp Log", fields=["date", "status", "reference_doctype", "reference_docname", "party", "mobile_number", "message"], order_by="date desc")
	
	return columns, data
