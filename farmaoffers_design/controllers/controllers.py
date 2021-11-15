#-*- coding: utf-8 -*-
from odoo import _, http
from odoo.http import request
from odoo.exceptions import UserError
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.payment.controllers.portal import PaymentProcessing
from werkzeug.exceptions import Forbidden, NotFound
from odoo.osv import expression
import base64
import logging

_logger = logging.getLogger(__name__)

# FO: Farma Offers

# Editing the sign up controller ""
class SignUpFO(AuthSignupHome):
    
    def _signup_with_values(self, token, values):
        context = self.get_auth_signup_qcontext()
        values.update({'street': context.get('address')})
        values.update({'phone': context.get('phone')})
        super(SignUpFO, self)._signup_with_values(token, values)

    @http.route(['/products/same-compounds'], type='json', website=True, auth='public', Sitemap=False)
    def get_all_products_with_same_compound(self, exception, compound=None, limit=None):
        products = http.request.env['product.template'].search([('id', '!=', exception), ('active_compound', '=', compound)], limit=limit)
        jsonProducts = []
        for product in products:
            jsonProducts.append({"id": product.id, "name": product.name, "website_url":product.website_url})

        return jsonProducts

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

    @http.route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True):
        res = super(website_sale_extend, self).cart_update_json(
            product_id=product_id, line_id=None, add_qty=add_qty, set_qty=set_qty, display=display)

        order = request.website.sale_get_order()

        res['farmaoffers_design.extend_table_cart'] = request.env['ir.ui.view']._render_template("farmaoffers_design.extend_table_cart", {
            'website_sale_order': order,
        })
        return res

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def address(self, **kw):
        Partner = request.env['res.partner'].with_context(show_address=1).sudo()
        order = request.website.sale_get_order()

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        mode = (False, False)
        can_edit_vat = False
        values, errors = {}, {}

        partner_id = int(kw.get('partner_id', -1))

        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            mode = ('new', 'billing')
            can_edit_vat = True
        # IF ORDER LINKED TO A PARTNER
        else:
            if partner_id > 0:
                if partner_id == order.partner_id.id:
                    mode = ('edit', 'billing')
                    can_edit_vat = order.partner_id.can_edit_vat()
                else:
                    shippings = Partner.search([('id', 'child_of', order.partner_id.commercial_partner_id.ids)])
                    if order.partner_id.commercial_partner_id.id == partner_id:
                        mode = ('new', 'shipping')
                        partner_id = -1
                    elif partner_id in shippings.mapped('id'):
                        mode = ('edit', 'shipping')
                    else:
                        return Forbidden()
                if mode and partner_id != -1:
                    values = Partner.browse(partner_id)
            elif partner_id == -1:
                mode = ('new', 'shipping')
            else: # no mode - refresh without post?
                return request.redirect('/shop/checkout')

        # IF POSTED
        if 'submitted' in kw:
            pre_values = self.values_preprocess(order, mode, kw)
            errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
            post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)

            if errors:
                errors['error_message'] = error_msg
                values = kw
            else:
                partner_id = self._checkout_form_save(mode, post, kw)
                if mode[1] == 'billing':
                    order.partner_id = partner_id
                    order.with_context(not_self_saleperson=True).onchange_partner_id()
                    # This is the *only* thing that the front end user will see/edit anyway when choosing billing address
                    order.partner_invoice_id = partner_id
                    if not kw.get('use_same'):
                        kw['callback'] = kw.get('callback') or \
                            (not order.only_services and (mode[0] == 'edit' and '/shop/checkout' or '/shop/address'))
                elif mode[1] == 'shipping':
                    order.partner_shipping_id = partner_id

                # TDE FIXME: don't ever do this
                order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
                if not errors:
                    return request.redirect(kw.get('callback') or '/shop/confirm_order?is_branch_office='+kw.get('is_branch_office'))

        render_values = {
            'website_sale_order': order,
            'partner_id': partner_id,
            'mode': mode,
            'checkout': values,
            'can_edit_vat': can_edit_vat,
            'error': errors,
            'callback': kw.get('callback'),
            'only_services': order and order.only_services,
        }
        render_values.update(self._get_country_related_render_values(kw, render_values))
        return request.render("website_sale.address", render_values)

    @http.route(['/shop/confirm_order'], type='http', auth="public", website=True, sitemap=False)
    def confirm_order(self, **post):

        order = request.website.sale_get_order()

        redirection = self.checkout_redirection(order) or self.checkout_check_address(order)
        if redirection:
            return redirection

        order.onchange_partner_shipping_id()
        order.order_line._compute_tax_id()
        request.session['sale_last_order_id'] = order.id
        request.website.sale_get_order(update_pricelist=True)
        extra_step = request.website.viewref('website_sale.extra_info_option')
        if extra_step.active:
            return request.redirect("/shop/extra_info")

        return request.redirect("/shop/payment?is_branch_office="+post.get('is_branch_office') if post.get('is_branch_office')== 'True' else "/shop/payment")

    @http.route(['/shop/payment'], type='http', auth="public", website=True, sitemap=False)
    def payment(self, **post):
        """ Payment step. This page proposes several payment means based on available
        payment.acquirer. State at this point :

         - a draft sales order with lines; otherwise, clean context / session and
           back to the shop
         - no transaction in context / session, or only a draft one, if the customer
           did go to a payment.acquirer website but closed the tab without
           paying / canceling
        """

        order = request.website.sale_get_order()
        carrier_id = post.get('carrier_id')
        if carrier_id:
            carrier_id = int(carrier_id)
        if order:
            order._check_carrier_quotation(force_carrier_id=carrier_id)
            if carrier_id:
                return request.redirect("/shop/payment")

        order = request.website.sale_get_order()
        redirection = self.checkout_redirection(order) or self.checkout_check_address(order)
        if redirection:
            return redirection

        render_values = self._get_shop_payment_values(order, **post)
        render_values['only_services'] = order and order.only_services or False

        if render_values['errors']:
            render_values.pop('acquirers', '')
            render_values.pop('tokens', '')
        if post.get('is_branch_office') == "True":
            render_values['is_branch_office'] = True

        return request.render("website_sale.payment", render_values)

class Quote(http.Controller):
    @http.route('/quote', auth='public', type='http', methods=['GET', 'POST'], website=True, sitemap=False)
    def quote(self, **kw):
        if request.httprequest.method == 'POST':
            _logger.warning("Data %s", kw)
            image = kw.get('upload', False)
            quote = request.env['farmaoffers.quote'].create({
                'name': kw.get('name'),
                'lastname': kw.get('lastname'),
                'city': kw.get('city'),
                'address': kw.get('address'),
                'phone': kw.get('phone'),
                'email': kw.get('email'),
                'description': kw.get('description'),
                'image': base64.encodestring(image.read()) if image else False
            })
            _logger.warning("Quote %s", quote.name)
            render_values = {
                'title':'Gracias!', 
                'body': quote.name +' estaremos contáctandole muy pronto', 
                'back_button_text': 'Volver al inicio', 
                'back_url': '/'
            }
            return http.request.render('farmaoffers_design.thanks_page', render_values)
        return http.request.render('farmaoffers_design.quote')