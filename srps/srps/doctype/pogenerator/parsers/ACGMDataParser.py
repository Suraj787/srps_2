#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from srps.srps.doctype.pogenerator.utils.PDFParser import PDFParser

class ACGMDataParser(object):

    def __init__(self, data, start_with):
        self.data = data
        self.cnt = 1
        self.final_data = {
            "po_details": {},
            "item_data": []
        }

        stw = start_with.split(',')
        self.stw = ' '.join(stw).split()

    def get_data_between(self, start_sep, end_sep):
        result = []
        tmp = self.data.split(start_sep)
        for par in tmp:
            if "START PAGE 0" in par:
                continue
            if end_sep in par:
                result.append(par.split(end_sep)[0])

        return result

    def get_text_between(self, data, start_sep, end_sep):
        result = []
        tmp = data.split(start_sep)
        for par in tmp:
            if "START PAGE 0" in par:
                continue
            if end_sep in par:
                result.append(par.split(end_sep)[0])

        return result

    def process_item_data(self):
        
        for text in self.stw:
            data_list = self.get_data_between(";{}".format(text), "m Total")
            for item in data_list:
                lines = item.split("\n")
                converted_data = self.convert_item_data(lines, start=text)
                if converted_data:
                    self.final_data["item_data"].append(converted_data)

    def process_po_information(self):

        data_list = self.get_data_between("PURCHASE ORDER", "Sl No")

        for item in data_list:
            lines = item.split("\n")
            converted_data = self.convert_po_information_data(lines)
            self.final_data["po_details"].update(converted_data)

        self.final_data

    def convert_item_data(self, data_list, start):

        qty = 0
        basic_price = 0
        material_code = ""
        del_date = ""
        drg_no = ""
        desc = ""
        hsn = ""

        for item in data_list:
            arr = item.split(";")

            if len(arr[0]) < 3:
                arr.pop(0)

            if "BasicPrice" in item:
                try:
                    qty = arr[1].split(' ')[0]
                except:
                    pass

                try:
                    material_code = "{}{}".format(start, arr[0])
                except:
                    pass

                try:
                    if len(arr) == 4:
                        basic_price = float(arr[3].replace(",", ""))
                    else:
                        basic_price = float(arr[4].replace(",", ""))
                except:
                    pass
            elif "Del." in item:
                if "Date" in arr[0]:
                    del_date = arr[0].split(":")[1]
                if "Date" in arr[1]:
                    del_date = arr[1].split(":")[1]

                try:

                    str_data = "".join(data_list)

                    new_data = self.get_text_between(str_data, 'BasicPrice;', 'Del.')

                    new_data = "".join(new_data)

                    if ";" in new_data:

                        desc = self.get_text_between(new_data, '.00 ', ';')
                        desc = " ".join(desc)
                    else:
                        desc = new_data.split('.00 ')[1]


                except Exception as es:
                    desc = ""

            elif "HSN" in item or "HS;N" in item:
                try:
                    hsn = item.split(":")[1].replace(" ","")
                except:
                    hsn = ""
            elif "Drg" in item:
                drg_no = arr[1].split(":")[1]

        if basic_price == 0:

            return None

        if drg_no == "":
            try:
                if len(material_code) == 14:
                    drg_no = "{}-{}".format(material_code.replace(" ","")[2:9], material_code.split("-")[1][:3])
                else:
                    drg_no = "{}-{}".format(material_code.replace(" ","")[2:8], material_code.split("-")[1][:3])
            except:
                drg_no = "{}-001".format(material_code.replace(" ","")[2:9])

        if qty == 0:

            return None

        data_dict = {
            "qty": qty,
            "basic_price": basic_price,
            "material_code": material_code.strip(),
            "del_date": del_date.strip(),
            "drg_no": drg_no.strip(),
            "desc": desc,
            "hsn": hsn,
        }
        return data_dict

    def convert_po_information_data(self, data_list):

        po_no = 0
        po_date = 0
        customer_name = ""
        buyer_name = ""

        for item in data_list:
            if item == "":
                continue

            arr = item.split(";")
            if "Range" in item or "Metalcrafts" in item:
                try:
                    customer_name = arr[0].split('.')[0]
                except:
                    pass

                if len(customer_name) < 2:
                        customer_name = item.replace(";", "")

            if "PO No" in item:
                try:
                    po_no = item.split(':')[1]
                except:
                    pass
            if "PO Date" in item:
                try:
                    po_date = item.split(':')[1]
                except:
                    pass
            if "Purchase Group" in item:
                try:
                    buyer_name = item.split(':')[2].split('-')[1]
                except:
                    pass


        data_dict = {
            "po_no": po_no.strip(),
            "po_date": po_date.strip(),
            "customer_name": customer_name.strip(),
            "buyer_name": buyer_name.strip(),
        }
        return data_dict

    def process(self):
        self.process_item_data()
        self.process_po_information()

        return self.final_data
