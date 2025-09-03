# -*- coding: utf-8 -*-
{
    'name': 'Panamá - Facturación electrónica y fiscal',
    'version': '14.0.3',
    'summary': 'Rootstack Intfiscal Software integration',
    'author': 'Rootstack',
    'website': 'www.rootstack.com',
    'depends': ['account' , 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/accounts_journals.xml',
        'views/res_partner.xml',
        'views/res_config_settings.xml',
        'views/account_move.xml',
        'views/res_company.xml',
        'views/account_journal.xml',
        'views/assets.xml',
        'wizard/ei_cancel_reason.xml'
    ],
    'qweb': [
        'static/src/xml/templates.xml'
    ],
    'installable': True,
    'auto_install': False,
    'external_dependencies': {
        "python": ['rootstack_ebi'],
    },
    'images': ['images/main_screenshot.png'],
    'price': 600.00,
    'currency': 'USD'
}
