# -*- coding: utf-8 -*-

{
    'name': 'Yappy Payment Acquirer',
    'category': 'Accounting/Payment Acquirers',
    'sequence': 365,
    'summary': 'Yappy Acquirer: Paypal Implementation',
    'version': '1.0',
    'description': """Yappy Payment Acquirer""",
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_yappy_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
    'application': True,
    'post_init_hook': '_post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
