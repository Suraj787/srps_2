#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from srps.srps.doctype.pogenerator.utils.PDFParser import PDFParser

class AccurateDataParser(object):

    def __init__(self, data):
        self.data = data
        self.cnt = 1
        self.final_data = {
            "po_details": {},
            "item_data": []
        }

        self.del_date = ""

    def get_data_between(self, start_sep, end_sep):
        result = []
        tmp = self.data.split(start_sep)
        for par in tmp:
            if end_sep in par:
                result.append(par.split(end_sep)[0])

        return result

    def get_text_between(self, data, start_sep, end_sep):
        result = []
        tmp = data.split(start_sep)
        for par in tmp:
            if end_sep in par:
                result.append(par.split(end_sep)[0])

        return result

    def process_item_data(self):
        data_list = self.get_data_between("Code;%", "Basic Order Value")
        for item in data_list:
            lines = item.split("\n")
            converted_data = self.convert_item_data(lines)
            self.final_data["item_data"] = converted_data

    def process_po_information(self):

        data_list = self.get_data_between("GSTIN/Uniquie ID :", "Insurance :")

        for item in data_list:
            lines = item.split("\n")
            converted_data = self.convert_po_information_data(lines)
            self.final_data["po_details"].update(converted_data)

        self.final_data

    def convert_item_data(self, data_list):

        tmp_list = []

        for idx, item in enumerate(data_list):

            qty = 0
            basic_price = 0
            material_code = ""
            del_date = self.del_date
            drg_no = ""
            desc = ""
            hsn = ""

            arr = item.split(";")
            if "GOODS" in item:
                try:
                    qty =  int(arr[5])
                    basic_price =  float(arr[7].replace(",",""))
                    material_code = arr[0].replace(" ","")[-11:]
                    
                    hsn = arr[2]
                    desc = arr[1]
                    try:
                        drg_text = data_list[(idx+1)]
                        if "Drg." in drg_text:
                            drg_data = drg_text.split(";")[1]
                            drg_data = drg_data.replace("Nos.","").replace("No. ","")
                            drg_no = drg_data.split(" ")[0]
                        else:
                            drg_no = "{}-P-{}-{}".format(material_code[4:6],material_code[6:8], material_code[8:])
                    except:
                        drg_no = ""

                except Exception as e:
                    pass

                data_dict = {
                    "qty": qty,
                    "basic_price": basic_price,
                    "material_code": material_code.strip(),
                    "del_date": del_date.strip(),
                    "drg_no": material_code.strip(),
                    "desc": "{}, Drg.No {}".format(desc, drg_no),
                    "hsn": hsn,
                }

                tmp_list.append(data_dict)

        return tmp_list

    def convert_po_information_data(self, data_list):

        po_no = ""
        po_date = ""
        customer_name = "Accurate Gauging & Instruments Pvt. Ltd."
        buyer_name = "K M Vatare"
        for item in data_list:
            arr = item.split(";")
            if "Order ;No." in item:
                try:
                    po_no = item.split(':')[1].replace(";","")
                except:
                    pass
            if "Date :     " in item:
                try:
                    po_date = item.split(':')[1].replace(";","").replace("-",".")
                    self.del_date = po_date
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
        self.process_po_information()
        self.process_item_data()

        return self.final_data
