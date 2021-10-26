#-*- coding: utf-8 -*-
from odoo import _, http
from odoo.http import request
from odoo.exceptions import UserError
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.osv import expression
import logging


_logger = logging.getLogger(__name__)

# class farmaoffers_design(http.Controller):
#     @http.route('/farmaoffers_design/farmaoffers_design/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/farmaoffers_design/farmaoffers_design/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('farmaoffers_design.listing', {
#             'root': '/farmaoffers_design/farmaoffers_design',
#             'objects': http.request.env['farmaoffers_design.farmaoffers_design'].search([]),
#         })

#     @http.route('/farmaoffers_design/farmaoffers_design/objects/<model("farmaoffers_design.farmaoffers_design"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('farmaoffers_design.object', {
#             'object': obj
#         })

# FO: Farma Offers

# Editing the sign up controller ""
class SignUpFO(AuthSignupHome):
    
    def _signup_with_values(self, token, values):
        context = self.get_auth_signup_qcontext()
        values.update({'street': context.get('address')})
        values.update({'phone': context.get('phone')})
        super(SignUpFO, self)._signup_with_values(token, values)

class website_sale_extend(WebsiteSale):

    def _check_float(self, val):
        try:
            return float(val)
        except ValueError:
            pass
        return False

    def _get_search_domain(self, search, category, attrib_values, search_in_description=True):
        domains = [request.website.sale_product_domain()]
        if search:
            for srch in search.split(" "):
                subdomains = [
                    [('name', 'ilike', srch)],
                    [('product_variant_ids.default_code', 'ilike', srch)]
                ]
                if search_in_description:
                    subdomains.append([('description', 'ilike', srch)])
                    subdomains.append([('description_sale', 'ilike', srch)])
                domains.append(expression.OR(subdomains))

        if category:
            domains.append([('public_categ_ids', 'child_of', int(category))])

        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domains.append([('attribute_line_ids.value_ids', 'in', ids)])
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domains.append([('attribute_line_ids.value_ids', 'in', ids)])
        
        domains = expression.AND(domains)
        # Brand
        brand = http.request.env['product.attribute'].sudo().search([('name', '=', 'Brand')], limit=1) or None
        if brand:
            search_brand = request.httprequest.args.get('search_brand')
            brand_name = http.request.env['product.attribute.value'].sudo().search([('name', '=', search_brand)], limit=1) or None
            if brand_name:
                domains = expression.AND([domains, [('attribute_line_ids.value_ids', 'in', [brand_name[0].id])]])
                
        # Price
        price_filter = None
        if http.request.env['price.filter'].sudo().search([], limit=1):
            price_filter = http.request.env['price.filter'].sudo().search([], limit=1)[0]
        min_price = request.httprequest.args.get('min_price')
        max_price = request.httprequest.args.get('max_price')

        if min_price:
            min_price = self._check_float(min_price)
            if min_price:
                domains = expression.AND([domains, [('list_price', '>=', min_price)]])
        if max_price:
            max_price = self._check_float(max_price)
            if max_price:
                domains = expression.AND([domains, [('list_price', '<=', max_price)]])
        if request.httprequest.args.get('under_10'):
            domains = expression.AND([domains, [('list_price', '<=', price_filter.price_under if price_filter else 10)]])
        if request.httprequest.args.get('ten_to_tweenty'):
            domains = expression.AND([domains, ['&',('list_price', '>=', price_filter.price_under if price_filter else 10), ('list_price', '<=', price_filter.price_over if price_filter else 20)]])
        if request.httprequest.args.get('over_20'):
            domains = expression.AND([domains, [('list_price', '>=', price_filter.price_over if price_filter else 20)]])
        _logger.info("DOMAINS %s" % (domains))
        return domains