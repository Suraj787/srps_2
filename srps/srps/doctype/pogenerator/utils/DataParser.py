#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from srps.srps.doctype.pogenerator.utils.PDFParser import PDFParser

class DataParser(object):

    def __init__(self, file_path, separator, threshold):
        self.file_path = file_path
        self.separator = separator
        self.threshold = threshold
        self.data = self.parse_csv_data()

    def parse_csv_data(self):
        parser = PDFParser()
        return parser.pdf_to_csv(self.file_path, self.separator, self.threshold)