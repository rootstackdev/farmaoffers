# -*- coding: utf-8 -*-
{
    'name': 'Panamá - Facturación electronica y fiscal POS',
    'version': '14.0.2',
    'author': 'Rootstack',
    'website': 'www.rootstack.com',
    'depends': ['account', 'point_of_sale', 'rootstack_intfiscal'],
    'installable': True,
    'auto_install': False,
    'data': [
        'views/templates.xml'
    ],
    'qweb': [
        'static/src/xml/FiscalPrintPopup.xml',
        'static/src/xml/ReceiptScreen.xml',
        'static/src/xml/ClientDetailsEdit.xml'
    ],
    'price': 400.00,
    'currency': 'USD',
    'images': ['images/main_screenshot.png']
}
