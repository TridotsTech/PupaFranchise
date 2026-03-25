
{% if not doc.is_return %} 
<center><p style="width:33%;border-bottom:0px;font-size:18px;text-align:center;"><b>INVOICE</b></p></center>
        {% else %}
<center><p style="width:33%;border-bottom:0px;font-size:18px;text-align:center;"><b>CREDIT NOTE</b></p></center>
        {% endif %}
<table style='border:1px solid black;width:100%;font-family:Arial, sans-serif;'>
   <tr style='width:100%;border-bottom:0px !important;'>
<td style='width:36%'>
    <nobr><p><b><span style="font-size: 18px;">{{ doc.company }} {% if doc.is_internal_customer != 1 %} {% if doc.branch %} - {{doc.branch or ""}}{% endif %} {% endif %}</span></b><br></nobr>
      {% if doc.branch %}
    {% set branch = frappe.get_doc("Branch", doc.branch) %}
    {% set ns = namespace(address=None) %}
    
    {% for table in branch.custom_company_wise_address_table %}
        {% if table.company == doc.company %}
            {% set ns.address = table.address %}
        {% endif %}
    {% endfor %}
    
    {% if ns.address %}
        {% set address_doc = frappe.get_doc("Address", ns.address) %}
        {{ address_doc.address_line1 or "" }}<br>
        {{ address_doc.address_line2 or "" }}<br>
        {{ address_doc.city or "" }}, {{ address_doc.state or "" }} - {{ address_doc.pincode or "" }}<br>
        {% if address_doc.email_id %} {{ address_doc.email_id }}<br> {% endif %}
        {% if address_doc.phone %} Mobile: {{ address_doc.phone }}<br> {% endif %}
        {% if address_doc.gstin %} GSTIN/UIN: {{ address_doc.gstin }} {% endif %}
    {% endif %}
{% endif %}

    </p>
</td>
       <!-- {% if not doc.is_return %} -->
       <!--<td style="width:33%;border-bottom:0px;font-size:22px;text-align:center;"><b>INVOICE</b></td>-->
       <!-- {% else %}-->
       <!-- <td style="width:33%;border-bottom:0px;font-size:22px;text-align:center;"><b>CREDIT NOTE</b></td>-->
       <!-- {% endif %}-->
       <td style="width:33%;border-top: 0px !important;text-align:right;">
       {% if doc.irn %}
            {% set e_invoice_log = frappe.db.get_value( "e-Invoice Log", doc.irn,
            ("invoice_data", "signed_qr_code"), as_dict=True ) %}
            <div style="padding-bottom:5px !important">
                <img width='120px' height='120px' src="data:image/png;base64,{{ get_qr_code(e_invoice_log.signed_qr_code, scale=2) }}" class="qrcode">
        		
        	</div>
        {% else %}
        
        {% endif %}
        </td>
   </tr>
   </table>
<table style="width: 100%; border: 1px solid black; border-collapse: collapse;font-family: Arial, sans-serif;">
   <tr style='border-bottom:0px !important; '>
      <tr style="border-bottom:none;line-height:0.4; border-right:1px solid black">
           <td colspan="5" >Invoice No  : <b>{{doc.name}}</b></td>
           <td colspan="6" style="text-align:right;border-right:1px solid black !important">Date : {{ frappe.utils.formatdate(doc.posting_date, "dd-mm-yyyy") }}
          {% set formatted_time = frappe.utils.get_time(doc.posting_time).strftime('%I:%M %p') %}
          {{ formatted_time }}</td>
     </tr>
     {% if doc.is_return and doc.custom_original_invoice_number %}
     <tr style="border-bottom:none;line-height:0.4;"><td colspan="5" >Original Invoice No :<b> {{doc.custom_original_invoice_number or "-"}}</b></td>
         
     </tr>
     {% endif %}
     {% if doc.ewaybill %}
     <tr style="border-bottom:none;line-height:0.4;border-right:1px solid black;">
        <td colspan="5" ><br>Eway-bill No: {{doc.ewaybill}} </td>
        <td colspan="5" style="border-right:1px solid black"></td>
     </tr>
     {% endif %}
     <!--<tr style="border-top:0px !important;border-bottom:0px !important;line-height:0.4;">-->
     <!--     <td colspan='10' >-->
          
          
          
     <!--     </td>-->
      </tr>
      <tr style="background-color:#333333;">
          <td colspan='7' ><b style="color:white;">Bill To</b></td>
          {% if doc.shipping_address_name %}
          {% set shipping_add = frappe.get_doc("Address", doc.shipping_address_name) %}
          {% endif %}
           {% if doc.dispatch_address_name %}
          {% set dispatch_add = frappe.get_doc("Address", doc.dispatch_address_name) %}
          {% endif %}
          
          <td colspan='7'style="border-right:1px solid black !important"> {% if dispatch_add %}<b style="color:white;">Dispatch From</b> {% elif shipping_add %} <b style="color:white;">Ship To</b> {% endif %}</td>
         
      </tr>
      <tr>
          {% if doc.customer_address %}
          {% set billing_add = frappe.get_doc("Address", doc.customer_address) %}
          {% endif %}
          {% if doc.shipping_address_name %}
          {% set shipping_add = frappe.get_doc("Address", doc.shipping_address_name) %}
          {% endif %}
          {%if doc.dispatch_address_name %}
          {% set dispatch_add = frappe.get_doc("Address", doc.dispatch_address_name) %}
          {% endif %}
          <td colspan='7' style="border-right:1px solid black !important">
          <b>{{doc.customer }}</b>
          <br>
            {% if billing_add %}
                {{ billing_add.address_line1 or "" }}<br>
                {% if billing_add.address_line2 %} {{ billing_add.address_line2 }}<br> {% endif %}
                {{ billing_add.city or "" }}<br>
                {{ billing_add.state or "" }} - {{ billing_add.pincode or "" }}<br>
                 {% if billing_add.gstin %} GSTIN/UIN: {{ billing_add.gstin }}<br> {% endif %}
                {% if billing_add.phone %} Mobile: {{ billing_add.phone }}{% elif frappe.db.get_value('Customer',doc.customer,'mobile_no') %} Mobile: {{ frappe.db.get_value('Customer',doc.customer,'mobile_no') }}<br> {% endif %}
               
            {% endif %}
          </td>
          
            {% if dispatch_add %}
             <td colspan='7' style='border-left:1px solid black; border-right:1px solid black'>
           <b>{{dispatch_add.address_title}}</b>
           <br>
            {{ dispatch_add.address_line1 or "" }}<br>
            {% if dispatch_add.address_line2 %} {{ dispatch_add.address_line2 }}<br> {% endif %}
            {{ dispatch_add.city or "" }}<br>
            {{ dispatch_add.state or "" }} - {{ dispatch_add.pincode or "" }}<br>
            {% if dispatch_add.gstin %} GSTIN/UIN: {{ dispatch_add.gstin }}<br> {% endif %}
            {% if dispatch_add.phone %} Mobile: {{ dispatch_add.phone }}<br> {% endif %}
            
           
            </td>
            {% elif shipping_add %}
          <td colspan='7' style='border-left:1px solid black; border-right:1px solid black'>
           <b>{{doc.customer }}</b>
           <br>
            {{ shipping_add.address_line1 or "" }}<br>
            {% if shipping_add.address_line2 %} {{ shipping_add.address_line2 }}<br> {% endif %}
            {{ shipping_add.city or "" }}<br>
            {{ shipping_add.state or "" }} - {{ shipping_add.pincode or "" }}<br>
            {% if shipping_add.gstin %} GSTIN/UIN: {{ shipping_add.gstin }} {% endif %}
            {% if shipping_add.phone %} Mobile: {{ shipping_add.phone }}<br> {% endif %}
            
            
            </td>
            {% else %}
            <td colspan='7' style='border-right:1px solid black'>

            
            {% endif %}
        </tr>
    </table>
    <table style="width: 100%; border: 1px solid black; border-collapse: collapse; table-layout: fixed; font-family: Arial, sans-serif;">

 
        <tr style="background-color:#333333;">
            <td style="width:6%; text-align:center;border-right:1px solid lightgrey;color:white;">S.No</td>
            <td style="width:10%;  text-align:center;border-right:1px solid lightgrey;color:white;">Image & Part No</td>
            <td colspan='2' style="width:15%; text-align:center;border-right:1px solid lightgrey;color:white;">Item & Description</td>
            <td style="width:10%; text-align:center;border-right:1px solid lightgrey;color:white;">HSN</td>
            <td style="width:9%; text-align:center;border-right:1px solid lightgrey;color:white;">Weight</td>
            <td style="width:7%; text-align:center;border-right:1px solid lightgrey;color:white;">Size</td>
            <td style="width:7%; text-align:center;border-right:1px solid lightgrey;color:white;">Qty</td>
            <td style="width:10%; text-align:center;border-right:1px solid lightgrey;color:white;">Rate</td>
            <td style="width:7%; text-align:center;border-right:1px solid lightgrey;color:white;"><nobr style='color:white;'>Dis %</nobr></td>
            <td style="width:20%; text-align:center;border-right:1px solid black;color:white;">Amount</td>

        
        </tr>
        
        {% for i in doc.items %}
    <tr>
  <td style="border-right:1px solid lightgrey;">{{ loop.index }}</td>

  <td style="text-align:center; border-right:1px solid lightgrey;">
    {% if i.image %}
      <img src="{{ i.image }}" style="max-width:50px; max-height:50px;">
    {% endif %}
    <br>{{ i.item_code or '' }}
  </td>

  <td style="border-right:1px solid lightgrey;" colspan='2' >{{ i.item_name or '' }}</td>

  <td style="text-align:center; border-right:1px solid lightgrey;">{{ i.gst_hsn_code or '' }}</td>

  <td style="text-align:center; border-right:1px solid lightgrey;">
    {{ i.weight_per_unit }}<br>{{ i.weight_uom or '' }}
  </td>

  <td style="text-align:center; border-right:1px solid lightgrey;">{{ i.custom_size or '' }}</td>

  <td style="text-align:center; border-right:1px solid lightgrey;">{{ abs(i.qty|int) }}</td>

  <td style="text-align:center; border-right:1px solid lightgrey;">{{ i.custom_mrp }}</td>

  <td style="text-align:center; border-right:1px solid lightgrey;">{{ '%.2f' % i.custom_mrp_discount_percentage }}%</td>

  <td style="text-align:right; border-right:1px solid black;" >
    <nobr>{{ frappe.utils.fmt_money(abs(i.amount), currency='INR') }}</nobr>
  </td>
</tr>

        {% endfor %}
        
        <tr style="border-top:1px solid lightgrey;border-right:1px solid black;border-left:1px solid black;">
            <td colspan='6' style='' >
              {% set tax_details = get_tax_table_sales_invoice(doc.doctype,doc.name) %}
              {% if tax_details.tax_rows | length %}
              <table style="width: 100%; border-collapse: collapse; color: black; font-size: 13px; line-height:0.6;">
                <thead>
                <tr style="border: 1px solid lightgrey; text-align: center; width: 10%;">
                   <th style="border: 1px solid lightgrey; width: 9%; background-color: white !important; color: black;">TAX%</th>
                   <th style="border: 1px solid lightgrey; width: 9%; text-align: center; background-color: white !important; color: black;">T.VALUE</th>
                   {% if tax_details.tax_category == 'In-State' %}
                   <th colspan="2" style="border: 1px solid lightgrey; width: 9%; text-align: center; background-color: white !important; color: black;">CGST</th>
                   <th colspan="2" style="border: 1px solid lightgrey; text-align: center; background-color: white !important; color: black;">SGST</th>
                   {% else %}
                   <th colspan="2" style="border: 1px solid lightgrey; text-align: center; background-color: white !important; color: black;">IGST</th>
                   {% endif %}
                </tr>
                </thead>
                <tbody>
                  {% for row in tax_details.tax_rows %}
                  <tr style="text-align: center;">
                    <td style="border: 1px solid lightgrey; width: 10%;">{{ row[0] ~ "%" }}</td>
                    <td style="border: 1px solid lightgrey; width: 10%;">{{ abs(row[1]) }}</td>
                    {% if tax_details.tax_category == 'In-State' %}
                    <td style="border: 1px solid lightgrey; width: 10%;">{{ row[2] ~ "%" }}</td>
                    <td style="border: 1px solid lightgrey; width: 25%;">{{ "" ~ abs(row[3]) }}</td>
                    <td style="border: 1px solid lightgrey; width: 10%;">{{ row[4] ~ "%" }}</td>
                    <td style="border: 1px solid lightgrey; width: 25%;">{{ " " ~ abs(row[5]) }}</td>
                    {% else %}
                    <td style="border: 1px solid lightgrey; width: 10%;">{{ row[6] ~ "%" }}</td>
                    <td style="border: 1px solid lightgrey; width: 20%;">{{ "" ~ abs(row[7] )}}</td>
                    {% endif %}
                 </tr>
                 {% endfor %}
                </tbody>
              </table>
              {% endif %}
              <b>In Words:</b><br>{{doc.in_words}}
            </td> 
            <td></td>            

            <td colspan='4'>
                <table style="width: 100%; border-collapse: collapse; border: 0px solid black; margin-left: 0px;line-height:0.5;">
                    <tr style="border-top:0px solid black;border-left:0px;border-bottom:0px;">
                        <td style="text-align:right;">
                            <strong>Net Value</strong>
                        </td>
                        <td style="text-align:right;">
                            <strong>₹{{ abs(doc.net_total) | round(2) }}</strong>
                        </td>
                    </tr>
            
                    {% set ns = namespace(total_sgst=0, total_cgst=0, total_igst=0) %}
                    {% for row in tax_details.tax_rows %}
                        {% set ns.total_cgst = ns.total_cgst + row[3] %}
                        {% set ns.total_sgst = ns.total_sgst + row[5] %}
                        {% set ns.total_igst = ns.total_igst + row[7] %}
                    {% endfor %}
            
                    {% if tax_details.tax_category == 'In-State' %}
                        <tr style="border-top:0px solid black;border-left:0px;border-bottom:0px;">
                            <td style="text-align: right; border: 0px solid black;"><strong>CGST</strong></td>
                            <td style="text-align: right; border: 0px solid black;"><b>₹{{ abs(ns.total_cgst) | round(2) }}</b></td>
                        </tr>
                        <tr style="border-top:0px solid black;border-left:0px;border-bottom:0px;">
                            <td style="padding: 5px; text-align: right; border: 0px solid black;"><strong>SGST</strong></td>
                            <td style="padding: 5px; text-align: right; border: 0px solid black;"><b>₹{{ abs(ns.total_sgst) | round(2) }}</b></td>
                        </tr>
                    {% else %}
                        <tr style="border-top:0px solid black;border-left:0px;border-bottom:0px;">
                            <td style="padding: 5px; text-align: right; border: 0px solid black;"><strong>IGST</strong></td>
                            <td style="padding: 5px; text-align: right; border: 0px solid black;"><b>₹{{ abs(ns.total_igst) | round(2) }}</b></td>
                        </tr>
                    {% endif %}
            
                    {% if doc.rounding_adjustment %}
                        <tr style="border-top:0px solid black;border-left:0px;border-bottom:0px;">
                            <td style="padding: 5px; text-align: right; border: 0px solid black;"><strong>Adjustment</strong></td>
                            <td style="padding: 5px; text-align: right; border: 0px solid black;"><b>₹{{ abs(doc.rounding_adjustment) | round(2) }}</b></td>
                        </tr>
                    {% endif %}
            
                    <tr style="border-top:0px solid black;border-left:0px;border-bottom:0px;">
                        <td style="padding: 5px; text-align: right; border: 0px solid black;"><strong>Total</strong></td>
                        <td style="padding: 5px; text-align: right; border: 0px solid black;"><strong>₹{{ abs(doc.rounded_total) | round(2) }}</strong></td>
                    </tr>
                    <!--<tr style="border-top:0px solid black;border-left:0px;border-bottom:0px;">-->
                    <!--    <td style="padding: 5px; text-align: right; border: 0px solid black;"><strong>Previous Balance</strong></td>-->
                    <!--    <td style="padding: 5px; text-align: right; border: 0px solid black;"><strong>₹{{ doc.custom_current_balance | round(2) }}</strong></td>-->
                    <!--</tr>-->
                    
                    <!--<tr style="border-top: 0px solid black; border-left: 0px; border-bottom: 0px;">-->
                    <!--    <td style="padding: 5px; text-align: right; border: 0px solid black;">-->
                    <!--        <strong>Total Balance</strong>-->
                    <!--    </td>-->
                    <!--    <td style="padding: 5px; text-align: right; border: 0px solid black;">-->
                    <!--        <strong>₹{{ (doc.custom_current_balance + doc.outstanding_amount) | round(2) }}</strong>-->
                    <!--    </td>-->
                    <!--</tr>-->

                </table>            
            </td>
        </tr>
{% if not doc.is_return %}
       <tr style="border:1px solid black;">
  <!-- Bank Details (Left Side) -->
  <td colspan="6" style="padding: 8px; vertical-align: top; border-right: 1px solid black;">
    <div style="font-size: 15px; background-color: #333; padding: 4px;">
      <b style="color: white;">Bank Details</b>
    </div>

    {% set branch = frappe.get_doc("Branch", doc.branch) if doc.branch else None %}

    {% if branch and branch.custom_company_wise_account_table %}
      {% for row in branch.custom_company_wise_account_table %}
      {% if row.company == doc.company and row.custom_use_in_print_format == 1 %}
        {% if row.bank_account %}
          {% set bank_account = frappe.get_doc("Bank Account", row.bank_account) %}
        {% else %}
          {% set bank_account = None %}
        {% endif %}

        {% if bank_account %}
        <table style="width: 100%; font-size: 12px; line-height: 0.5; margin-top: 5px;">
          <tr>
            <td style="width: 40%;"><strong>Account Number</strong></td>
            <td>: {{ bank_account.bank_account_no }}</td>
          </tr>
          <tr>
            <td><strong>Bank Name</strong></td>
            <td>: {{ bank_account.bank }}</td>
          </tr>
          <tr>
            <td><strong>IFSC Code</strong></td>
            <td>: {{ bank_account.branch_code }}</td>
          </tr>
          <tr>
            <td><strong>Branch</strong></td>
            <td>: {{ bank_account.custom_branch_name }}</td>
          </tr>
        </table>
        {% else %}
          <div style="padding: 5px; color: red; font-weight: bold;">Kindly update the bank details.</div>
        {% endif %}
        {% endif %}
      {% endfor %}
    {% else %}
      <div style="padding: 5px; color: red; font-weight: bold;">Kindly update the branch details.</div>
    {% endif %}
  </td>

  <!-- QR Code (Right Side) -->
  <td colspan="5" style="text-align: center; vertical-align: middle;">
    {% if doc.branch %}
      {% set branch = frappe.get_doc("Branch", doc.branch) %}
      {% for row in branch.custom_company_wise_account_table %}
      {% if row.company == doc.company and row.custom_use_in_print_format == 1 %}
        {% set bank_account = frappe.get_doc("Bank Account", row.bank_account) if row.bank_account else None %}
        {% if bank_account and bank_account.custom_qr_code %}
    
          <img src="{{ frappe.utils.get_url() }}{{ bank_account.custom_qr_code }}" style="width: 100px; height: 100px;">
        {% else %}
          <p>No QR Code Available</p>
        {% endif %}
      {% endif %}
      {% endfor %}
    {% else %}
      <p>No QR Code Available</p>
    {% endif %}
  </td>
</tr>
      {% endif %}
      <tr>
          <td colspan="7" ><b style="font-size:13px;">{% if not doc.is_return %}Terms and Conditions:</b><br>
          Payment made by cash to company staff's will not be considered as payment<br>
           & not responsible for that amount<br>
          <div style='font-size:14px;width:75%;'><b>Only payment made on cheque/NEFT/RTGS</b></div>
          Goods once accepted will not be taken back in cash discrepancy it should returned with in 7 days
          {% endif %}</td>
          <td colspan='4' style="text-align:right;">
              <b>For {{doc.company}}</b>
          <br><br><br><br>
          Authorised Signatory
          </td>
      </tr>
</table>
