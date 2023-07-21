# -*- coding: utf-8 -*-
{
    'name': "FarmaOffers Module",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '14.0.7',

    # any module necessary for this one to work correctly
    'depends': ['base', 'website', 'website_sale', 'website_sale_delivery', 'theme_grocery', 'point_of_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/h_f_templates.xml',
        'views/snippets.xml',
        'views/inherit_templates.xml',
        'views/homepage_templates.xml',
        'views/delivery_carrier.xml',
        'views/address_template.xml',
        'views/sale_order.xml',
        'views/res_country_state.xml',
        'views/website_form_templates_inherit.xml',
        'views/website_data_inherit.xml',
        'views/res_config_settings_views.xml',
        'data/res_country_data.xml',
        'views/res_partner_view.xml',
        'views/portal_templates.xml',
        'views/website_top_slider_views.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'installable': True,
    'application': True,
}
