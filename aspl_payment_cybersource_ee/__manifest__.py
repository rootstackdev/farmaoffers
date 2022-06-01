# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
{
    'name': 'Odoo CyberSource Payment Gateway (Enterprise)',
    'summary': 'Cybersource Payment Gateway',
    'version': '1.0',
    'description': """Cybersource Payment Gateway""",
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'category': 'Website',
    'website': "http://www.acespritech.com",
    'price': 50.00,
    'currency': 'EUR',
    'depends': ['payment'],
    'data': [
        'views/payment_view.xml',
        'views/payment_cybersource_template.xml',
        'data/payment_acquirer_data.xml',
    ],
    'images': ['static/description/cyber_source_logo.jpg'],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
