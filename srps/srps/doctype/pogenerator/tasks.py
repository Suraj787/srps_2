#!/usr/bin/env python
# -*- coding: utf-8 -*-
import frappe

def all():

    emails = frappe.get_list('Communication', filters={
                             "communication_type": "Communication", 
                             "communication_medium": "Email", 
                             "sent_or_received": "Received", 
                             "seen": 0}
                             )

    print "*"*100
    print "Running POGenerator email sync"
    print "*"*100

    for email in emails:

        email_obj = frappe.get_doc('Communication', email.get('name'))

        files = frappe.get_list('File', filters={'attached_to_name':email_obj.get('name')})

        can_skip = False
	check_file_name = False
        if "Purchase Order Number" in email_obj.subject:
            can_skip = False
        elif "accurategauging.com" in email_obj.sender:
            can_skip = False
            check_file_name = True
        else:
            can_skip = True

        if can_skip:
            email_obj.seen = 1
            email_obj.save()
            frappe.db.commit()
            continue

        for file in files:

            file_obj = frappe.get_doc('File', file.get('name'))

            if not ".pdf" in file_obj.file_name:
                continue
            #if check_file_name:
            #    if not "shreeram" in file_obj.file_name.lower():
            #        continue
            try:
                pog = frappe.get_doc({"doctype":"POGenerator"}).insert()

                pog.pdf_file = "/files/{}".format(file_obj.file_name)

                pog.source = "Email"

                pog.save()

            except:
                pass

        email_obj.seen = 1

        email_obj.save()
        frappe.db.commit()
