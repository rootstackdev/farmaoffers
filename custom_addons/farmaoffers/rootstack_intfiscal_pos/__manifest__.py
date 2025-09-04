# -*- coding: utf-8 -*-
{
    'name': 'Panamá - Facturación electronica y fiscal POS',
    'version': '18.0.1.0',
    'author': 'Rootstack',
    'website': 'www.rootstack.com',
    'depends': ['account', 'point_of_sale', 'rootstack_intfiscal'],
    'installable': True,
    'auto_install': False,
    'assets': {
        'point_of_sale.assets': [
            'rootstack_intfiscal_pos/static/src/xml/FiscalPrintPopup.xml',
            'rootstack_intfiscal_pos/static/src/xml/ReceiptScreen.xml',
            'rootstack_intfiscal_pos/static/src/xml/ClientDetailsEdit.xml',
            'rootstack_intfiscal_pos/static/src/css/styles.css',
        ],
    },
    'price': 400.00,
    'currency': 'USD',
    'images': ['images/main_screenshot.png']
}
