#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2018, Satish Aralkar and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.website.website_generator import WebsiteGenerator
from srps.srps.doctype.pogenerator.utils.DataParser import DataParser
from srps.srps.doctype.pogenerator.parsers import ACGPDataParser, AccurateDataParser, ACGMDataParser
import datetime
from datetime import timedelta

import sys
import shutil

reload(sys)  
sys.setdefaultencoding('utf8')

class POGenerator(Document):

    def on_update(self):

        if self.generated == "No" and self.pdf_file:

            file_path = frappe.__path__[0]
            file_path = file_path.split('/apps')[0]
            pdf_file = frappe.utils.file_manager.get_file_path(self.pdf_file)

            file_full_path = "{}/sites/{}".format(file_path, pdf_file)

            if self.source == "Email":

                tmp_file_full_path = file_full_path.replace('/public/','/private/')

                shutil.copy2(tmp_file_full_path, file_full_path)

            separator = ';'

            threshold = 1.5

            data_parser = DataParser(file_full_path, separator, threshold)

            data =  data_parser.data

            file_data = None

            maintain_stock = "0"

            if "PAMPAC" in data:

                parsed_data_obj = ACGPDataParser.ACGPDataParser(data, self.start_with)

                maintain_stock = "1"

                file_data = parsed_data_obj.process()

            if "Metalcrafts" in data:

                parsed_data_obj = ACGMDataParser.ACGMDataParser(data, self.start_with)

                maintain_stock = "1"

                file_data = parsed_data_obj.process()

            elif "27AABCA5153C1Z5" in data:

                parsed_data_obj = AccurateDataParser.AccurateDataParser(data)

                maintain_stock = "1"

                file_data = parsed_data_obj.process()

            customer = None
            if not frappe.db.exists("Customer", file_data.get('po_details').get('customer_name')):
                customer = frappe.get_doc({"doctype": "Customer", "customer_name": file_data.get(
                    'po_details').get('customer_name')})
                customer.save(ignore_permissions=True)
            else:
                customer = frappe.get_doc("Customer", file_data.get(
                    'po_details').get('customer_name'))

            so_items = []

            total = 0

            po_date = file_data.get('po_details').get('po_date').replace(".","-")

            try:

                po_date = datetime.datetime.strptime(po_date, "%d-%m-%Y").date()

            except:

                po_date = datetime.datetime.strptime(po_date, "%d-%m-%y").date()

            for item in file_data.get("item_data", []):

                tmp_item = None

                drg_no = item.get("drg_no")

                material_code = item.get("material_code")

                total += int(item.get("basic_price"))

                rate = int(item.get("basic_price"))/int(item.get("qty"))

                if drg_no == "":

                    drg_no = item.get("material_code")

                if not frappe.db.exists("Item", material_code):

                    tmp_item = frappe.get_doc(
                        {"doctype": "Item", "item_code": material_code, "item_group": "All Item Groups"}).insert()
                    tmp_item.standard_rate = int(item.get("basic_price"))/int(item.get("qty"))
                    tmp_item.stock_uom = "Nos"
                    tmp_item.name = item.get("material_code")
                    tmp_item.is_stock_item = maintain_stock
                    if item.get("desc"):
                        tmp_item.description = item.get("desc")
                    if item.get("hsn"):
                        if not frappe.db.exists("GST HSN Code", item.get("hsn")):
                            hsn_obj = frappe.get_doc({"doctype": "GST HSN Code", "hsn_code": item.get("hsn")}).insert()
                            hsn_obj.save()
                        else:
                            hsn_obj = frappe.get_doc("GST HSN Code", item.get("hsn"))

                        tmp_item.gst_hsn_code = hsn_obj.hsn_code
                    tmp_item.save()

                else:

                    tmp_item = frappe.get_doc("Item", material_code)

                item_date = item.get('del_date').replace(".","-")

                try:
                    item_date = datetime.datetime.strptime(item_date, "%d-%m-%Y").date()
                except:
                    item_date = datetime.datetime.strptime(item_date, "%d-%m-%y").date()

                new_item = frappe.get_doc({"doctype": "Sales Order Item", "base_amount": item.get("basic_price"), "item_code": tmp_item.name, "item_name": tmp_item.name, "parentfield": "items", "qty": item.get(
                    "qty"), "description": tmp_item.description, "conversion_factor": 1.0, "uom": "Nos", "parent": self.name, "wearhouse": "Stores - T VS", "parenttype": 'Sales Order', 'delivery_date': item_date, 'rate': rate}).insert()

                so_items.append(new_item)

            sales_order = frappe.get_doc({"doctype": "Sales Order", "customer": customer.customer_name, "delivery_date": po_date, "items": so_items}).insert()

            sales_order.total = total
            sales_order.net_total = total
            sales_order.base_grand_total = total
            sales_order.base_net_total = total
            sales_order.po_no = file_data.get('po_details').get('po_no')
            sales_order.po_date = po_date

            sales_order.save()

            for item in so_items:

                item.parent = sales_order.name

                if 'prod_delivery_date' in dir(item):

                    days = int(item.no_of_days)

                    item.prod_delivery_date = item.delivery_date - timedelta(days=days)  

                item.save()

            frappe.db.sql("DELETE FROM `tabSales Order Item` WHERE parent=%s", self.name)

            self.sales_order = sales_order.name

            self.generated = "Yes"

            self.save()

