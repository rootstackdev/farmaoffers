# -*- coding: utf-8 -*-
from odoo import _, http
from odoo.http import request
from odoo.exceptions import UserError
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.payment.controllers.portal import PaymentProcessing
from werkzeug.exceptions import Forbidden, NotFound
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.website_sale.controllers.main import Website
from odoo.osv import expression
from odoo.addons.http_routing.models.ir_http import slug
import base64
import logging
import re
import werkzeug

# Make a regular expression
# for validating an Email
regexEmail = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
#regexName =r'/^[\w\s]+$/'

_logger = logging.getLogger(__name__)


class Website(Website):

    @http.route()
    def index(self, **kw):
        Category = request.env['product.public.category'].sudo()
        website_domain = request.website.website_domain()
        categs_domain = [('parent_id', '=', False)] + website_domain
        categs = Category.search(categs_domain)
        res = super().index(**kw)
        _logger.error(type(request.httprequest.user_agent.browser))
        res.qcontext.update({
            'categories': categs,
            'slug': slug,
        })
        return res


class SignUpFO(AuthSignupHome):

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        errors = validator(qcontext)
        if len(errors) > 0:
            qcontext["error"] = [qcontext["error"]] + \
                errors if 'error' in qcontext else errors

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                # Send an account creation confirmation email
                if qcontext.get('token'):
                    User = request.env['res.users']
                    user_sudo = User.sudo().search(
                        User._get_login_domain(qcontext.get('login')), order=User._get_login_order(), limit=1
                    )
                    template = request.env.ref(
                        'auth_signup.mail_template_user_signup_account_created', raise_if_not_found=False)
                    if user_sudo and template:
                        template.sudo().send_mail(user_sudo.id, force_send=True)
                return self.web_login(*args, **kw)
            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _(
                        "Another user is already registered using this email address.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _("Could not create a new account.")

        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_reset_password(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get('token') and not qcontext.get('reset_password_enabled'):
            raise werkzeug.exceptions.NotFound()

        errors = validator(qcontext, qcontext.get('token'))
        if len(errors) > 0:
            qcontext["error2"] = errors

        if 'error' not in qcontext and 'error2' not in qcontext and request.httprequest.method == 'POST':
            try:
                if qcontext.get('token'):
                    self.do_signup(qcontext)
                    return self.web_login(*args, **kw)
                else:
                    login = qcontext.get('login')
                    assert login, _("No login provided.")
                    _logger.info(
                        "Password reset attempt for <%s> by user <%s> from %s",
                        login, request.env.user.login, request.httprequest.remote_addr)
                    request.env['res.users'].sudo().reset_password(login)
                    qcontext['message'] = _(
                        "An email has been sent with credentials to reset your password")
            except UserError as e:
                qcontext['error'] = e.args[0]
            except SignupError:
                qcontext['error'] = _("Could not reset your password")
                _logger.exception('error when resetting password')
            except Exception as e:
                qcontext['error'] = str(e)

        response = request.render('auth_signup.reset_password', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    def _signup_with_values(self, token, values):
        context = self.get_auth_signup_qcontext()
        values.update({'street': context.get('address')})
        values.update({'phone': context.get('phone')})
        super(SignUpFO, self)._signup_with_values(token, values)

    @http.route(['/products/same-compounds'], type='json', website=True, auth='public', Sitemap=False)
    def get_all_products_with_same_compound(self, exception, compound=None, limit=None):
        products = http.request.env['product.template'].search(
            [('id', '!=', exception), ('active_compound', '=', compound)], limit=limit)
        jsonProducts = []
        for product in products:
            jsonProducts.append(
                {"id": product.id, "name": product.name, "website_url": product.website_url})

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
                    [('product_variant_ids.default_code', 'ilike', srch)],
                    [('active_compound', 'ilike', srch)],
                    [('laboratory', 'ilike', srch)]
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
                    domains.append(
                        [('attribute_line_ids.value_ids', 'in', ids)])
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domains.append([('attribute_line_ids.value_ids', 'in', ids)])

        domains = expression.AND(domains)
        # Brand
        brand = http.request.env['product.attribute'].sudo().search(
            [('name', '=', 'Brand')], limit=1) or None
        if brand:
            search_brand = request.httprequest.args.get('search_brand')
            brand_name = http.request.env['product.attribute.value'].sudo().search(
                [('name', '=', search_brand)], limit=1) or None
            if brand_name:
                domains = expression.AND(
                    [domains, [('attribute_line_ids.value_ids', 'in', [brand_name[0].id])]])

        # Price
        price_filter = None
        if http.request.env['price.filter'].sudo().search([], limit=1):
            price_filter = http.request.env['price.filter'].sudo().search([], limit=1)[
                0]
        min_price = request.httprequest.args.get('min_price')
        max_price = request.httprequest.args.get('max_price')

        if min_price:
            min_price = self._check_float(min_price)
            if min_price:
                domains = expression.AND(
                    [domains, [('list_price', '>=', min_price)]])
        if max_price:
            max_price = self._check_float(max_price)
            if max_price:
                domains = expression.AND(
                    [domains, [('list_price', '<=', max_price)]])
        if request.httprequest.args.get('under_10'):
            domains = expression.AND(
                [domains, [('list_price', '<=', price_filter.price_under if price_filter else 10)]])
        if request.httprequest.args.get('ten_to_tweenty'):
            domains = expression.AND([domains, ['&', ('list_price', '>=', price_filter.price_under if price_filter else 10), (
                'list_price', '<=', price_filter.price_over if price_filter else 20)]])
        if request.httprequest.args.get('over_20'):
            domains = expression.AND(
                [domains, [('list_price', '>=', price_filter.price_over if price_filter else 20)]])
        _logger.info("DOMAINS %s" % (domains))
        return domains

    @http.route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, product_id=None, line_id=None, add_qty=None, set_qty=None, display=True):
        res = super(website_sale_extend, self).cart_update_json(
            product_id=product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty, display=display)

        order = request.website.sale_get_order()

        res['farmaoffers_design.extend_table_cart'] = request.env['ir.ui.view']._render_template("farmaoffers_design.extend_table_cart", {
            'website_sale_order': order,
        })
        return res

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def address(self, **kw):
        Partner = request.env['res.partner'].with_context(
            show_address=1).sudo()
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
                    shippings = Partner.search(
                        [('id', 'child_of', order.partner_id.commercial_partner_id.ids)])
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
            else:  # no mode - refresh without post?
                return request.redirect('/shop/checkout')

        # IF POSTED
        if 'submitted' in kw:
            pre_values = self.values_preprocess(order, mode, kw)
            errors, error_msg = self.checkout_form_validate(
                mode, kw, pre_values)
            post, errors, error_msg = self.values_postprocess(
                order, mode, pre_values, errors, error_msg)

            if errors:
                errors['error_message'] = error_msg
                values = kw
            else:
                partner_id = self._checkout_form_save(mode, post, kw)
                if mode[1] == 'billing':
                    order.partner_id = partner_id
                    order.with_context(
                        not_self_saleperson=True).onchange_partner_id()
                    # This is the *only* thing that the front end user will see/edit anyway when choosing billing address
                    order.partner_invoice_id = partner_id
                    if not kw.get('use_same'):
                        kw['callback'] = kw.get('callback') or \
                            (not order.only_services and (
                                mode[0] == 'edit' and '/shop/checkout' or '/shop/address'))
                elif mode[1] == 'shipping':
                    order.partner_shipping_id = partner_id

                # TDE FIXME: don't ever do this
                order.message_partner_ids = [
                    (4, partner_id), (3, request.website.partner_id.id)]
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
            'only_services': order and order.only_services
        }
        render_values.update(
            self._get_country_related_render_values(kw, render_values))
        return request.render("website_sale.address", render_values)

    """ Inherit function to add zones field if country code is PA """

    def _get_country_related_render_values(self, kw, render_values):
        res = super()._get_country_related_render_values(kw, render_values)
        if request.website.sudo().company_id.country_id.code == "PA":
            country = res["country"]
            if country and country.code == "PA":
                states = res.get("country_states", False)
                if states and len(states) == 1:
                    res.update({
                        "zones": states[0].get_website_sale_zones()
                    })
        return res

    @http.route(['/shop/confirm_order'], type='http', auth="public", website=True, sitemap=False)
    def confirm_order(self, **post):

        order = request.website.sale_get_order()

        redirection = self.checkout_redirection(
            order) or self.checkout_check_address(order)
        if redirection:
            return redirection

        order.onchange_partner_shipping_id()
        order.order_line._compute_tax_id()
        request.session['sale_last_order_id'] = order.id
        request.website.sale_get_order(update_pricelist=True)
        extra_step = request.website.viewref('website_sale.extra_info_option')
        if extra_step.active:
            return request.redirect("/shop/extra_info")

        return request.redirect("/shop/payment?is_branch_office="+post.get('is_branch_office') if post.get('is_branch_office') == 'True' else "/shop/payment")

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
        shipping_mode = 'address'
        order = request.website.sale_get_order()
        carrier_id = post.get('carrier_id')
        if carrier_id:
            carrier_id = int(carrier_id)
        if order and not post.get('is_branch_office'):
            order._check_carrier_quotation(force_carrier_id=carrier_id)
            if carrier_id:
                return request.redirect("/shop/payment")

        redirection = self.checkout_redirection(
            order) or self.checkout_check_address(order)
        if redirection:
            return redirection

        render_values = self._get_shop_payment_values(order, **post)
        render_values['only_services'] = order and order.only_services or False
        if post.get('is_branch_office') == "True":
            order._remove_delivery_line()
            shipping_mode = 'branch'
            render_values['is_branch_office'] = True

        if render_values['errors']:
            render_values.pop('acquirers', '')
            render_values.pop('tokens', '')
        order.shipping_mode = shipping_mode

        return request.render("website_sale.payment", render_values)

    def _get_shop_payment_values(self, order, **kwargs):
        values = super(website_sale_extend, self)._get_shop_payment_values(order, **kwargs)
        if kwargs.get('is_branch_office'):
            values['errors'] = [item for item in values['errors'] if item[0] != _('Sorry, we are unable to ship your order')]
        return values

    @http.route(['/shop/payment/transaction/',
                 '/shop/payment/transaction/<int:so_id>',
                 '/shop/payment/transaction/<int:so_id>/<string:access_token>'], type='json', auth="public", website=True)
    def payment_transaction(self, acquirer_id, save_token=False, so_id=None, access_token=None, token=None, **kwargs):
        """ Json method that creates a payment.transaction, used to create a
        transaction when the user clicks on 'pay now' button. After having
        created the transaction, the event continues and the user is redirected
        to the acquirer website.

        :param int acquirer_id: id of a payment.acquirer record. If not set the
                                user is redirected to the checkout page
        """
        # Ensure a payment acquirer is selected
        if not acquirer_id:
            return False

        try:
            acquirer_id = int(acquirer_id)
        except:
            return False

        # Retrieve the sale order
        if so_id:
            env = request.env['sale.order']
            domain = [('id', '=', so_id)]
            if access_token:
                env = env.sudo()
                domain.append(('access_token', '=', access_token))
            order = env.search(domain, limit=1)
        else:
            order = request.website.sale_get_order()

        # Ensure there is something to proceed
        if not order or (order and not order.order_line):
            return False

        assert order.partner_id.id != request.website.partner_id.id

        if kwargs['is_branch_office'] == "True" and kwargs['branch_office_id'] != "0":
            order.branch_office_id = kwargs['branch_office_id']

        # Create transaction
        vals = {'acquirer_id': acquirer_id,
                'return_url': '/shop/payment/validate'}

        if save_token:
            vals['type'] = 'form_save'
        if token:
            vals['payment_token_id'] = int(token)

        transaction = order._create_payment_transaction(vals)

        # store the new transaction into the transaction list and if there's an old one, we remove it
        # until the day the ecommerce supports multiple orders at the same time
        last_tx_id = request.session.get('__website_sale_last_tx_id')
        last_tx = request.env['payment.transaction'].browse(
            last_tx_id).sudo().exists()
        if last_tx:
            PaymentProcessing.remove_payment_transaction(last_tx)
        PaymentProcessing.add_payment_transaction(transaction)
        request.session['__website_sale_last_tx_id'] = transaction.id
        return transaction.render_sale_button(order, render_values={
            "amount_tax": order.amount_tax,
            "amount_delivery": order.amount_delivery,
            "amount_untaxed": order.amount_untaxed
        })

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', ppg=False, **post):

        add_qty = int(post.get('add_qty', 1))
        Category = request.env['product.public.category']
        if category:
            category = Category.search([('id', '=', int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = Category

        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg or 20

        ppr = request.env['website'].get_current_website().shop_ppr or 4

        if post.get('show'):
            ppg = int(post.get('show'))

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")]
                         for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}

        domain = self._get_search_domain(search, category, attrib_values)

        keep = QueryURL('/shop', category=category and int(category),
                        search=search, attrib=attrib_list, order=post.get('order'))

        pricelist_context, pricelist = self._get_pricelist_context()

        request.context = dict(
            request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        url = "/shop"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list

        Product = request.env['product.template'].with_context(bin_size=True)

        search_product = Product.search(
            domain, order=self._get_search_order(post))
        website_domain = request.website.website_domain()
        categs_domain = [('parent_id', '=', False)] + website_domain
        if search:
            search_categories = Category.search(
                [('product_tmpl_ids', 'in', search_product.ids)] + website_domain).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
        else:
            search_categories = Category
        categs = Category.search(categs_domain)

        if category:
            url = "/shop/category/%s" % slug(category)

        product_count = len(search_product)
        pager = request.website.pager(
            url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        offset = pager['offset']
        products = search_product[offset: offset + ppg]

        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            attributes = ProductAttribute.search(
                [('product_tmpl_ids', 'in', search_product.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)

        layout_mode = request.session.get('website_sale_shop_layout_mode')
        if not layout_mode:
            if request.website.viewref('website_sale.products_list_view').active:
                layout_mode = 'list'
            else:
                layout_mode = 'grid'

        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'add_qty': add_qty,
            'products': products,
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, ppg, ppr),
            'ppg': ppg,
            'ppr': ppr,
            'categories': categs,
            'attributes': attributes,
            'keep': keep,
            'search_categories_ids': search_categories.ids,
            'layout_mode': layout_mode,
        }
        if category:
            values['main_object'] = category

        # them Grocery
        att_items = values['attrib_values']
        new_list = {}
        for item in att_items:
            if item[0] in new_list.keys():
                att_value = new_list.get(item[0])
                att_value += [item[1]]
                new_list[item[0]] = att_value
            else:
                new_list.update({item[0]: [item[1]]})

        attr_filters = {}
        for attr in new_list:
            attr_name = request.env['product.attribute'].browse(attr).name
            attr_values = []
            for att_value_id in new_list.get(attr):
                attr_value = request.env['product.attribute.value'].browse(
                    att_value_id).name
                attr_values.append((attr_value, '%s-%s' %
                                   (attr, att_value_id)))
            attr_filters.update({attr_name: attr_values})
        values['attr_filters'] = attr_filters

        return request.render("website_sale.products", values)

    @http.route('/shop/products/autocomplete', type='json', auth='public', website=True)
    def products_autocomplete(self, term, options={}, **kwargs):
        """
        Returns list of products according to the term and product options

        Params:
            term (str): search term written by the user
            options (dict)
                - 'limit' (int), default to 5: number of products to consider
                - 'display_description' (bool), default to True
                - 'display_price' (bool), default to True
                - 'order' (str)
                - 'max_nb_chars' (int): max number of characters for the
                                        description if returned

        Returns:
            dict (or False if no result)
                - 'products' (list): products (only their needed field values)
                        note: the prices will be strings properly formatted and
                        already containing the currency
                - 'products_count' (int): the number of products in the database
                        that matched the search query
        """
        ProductTemplate = request.env['product.template']

        display_description = False  # options.get('display_description', True)
        display_price = options.get('display_price', True)
        order = self._get_search_order(options)
        max_nb_chars = options.get('max_nb_chars', 999)

        category = options.get('category')
        attrib_values = options.get('attrib_values')
        # display_description
        domain = self._get_search_domain(term, category, attrib_values)
        products = ProductTemplate.search(
            domain,
            limit=min(20, options.get('limit', 5)),
            order=order
        )

        fields = ['id', 'name', 'website_url']
        if display_description:
            fields.append('description_sale')

        res = {
            'products': products.read(fields),
            'products_count': ProductTemplate.search_count(domain),
        }

        if display_description:
            for res_product in res['products']:
                desc = res_product['description_sale']
                if desc and len(desc) > max_nb_chars:
                    res_product['description_sale'] = "%s..." % desc[:(
                        max_nb_chars - 3)]

        if display_price:
            FieldMonetary = request.env['ir.qweb.field.monetary']
            monetary_options = {
                'display_currency': request.website.get_current_pricelist().currency_id,
            }
            for res_product, product in zip(res['products'], products):
                combination_info = product._get_combination_info(
                    only_template=True)
                res_product.update(combination_info)
                res_product['list_price'] = FieldMonetary.value_to_html(
                    res_product['list_price'], monetary_options)
                res_product['price'] = FieldMonetary.value_to_html(
                    res_product['price'], monetary_options)

        return res

    @http.route(['/shop/update_shipping_mode'], type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def update_eshop_shipping_mode(self, **post):
        mode = post.get('mode')
        order = request.website.sale_get_order()
        order.shipping_mode = mode
        if mode == 'branch':
            order._remove_delivery_line()
        if mode == 'address':
            order._check_carrier_quotation()
        post['carrier_id'] = 0
        return self._update_website_sale_delivery_return(order, **post)

    @http.route(['/shop/state_infos/<int:state_id>'], type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def state_infos(self, state_id):
        return request.env['l10n.pa.delivery.zone'].search_read([('state_id', '=', state_id)], ['name'])

    @http.route(['/shop/country_infos/<model("res.country"):country>'], type='json', auth="public", methods=['POST'], website=True)
    def country_infos(self, country, mode, **kw):
        country_infos = super(website_sale_extend, self).country_infos(
            country=country, mode=mode, **kw)
        zones = []
        if len(country_infos['states']) > 0:
            zones = [(zone.id, zone.name) for zone in request.env['res.country.state'].browse(
                country_infos['states'][0][0]).get_website_sale_zones()]
        country_infos['zones'] = zones
        return country_infos


class CustomerPortalFO(CustomerPortal):

    def details_form_validate(self, data):
        error, error_message = super(
            CustomerPortalFO, self).details_form_validate(data)

        # phone validation
        if data.get('phone') and not data.get('phone').isdigit() and not (len(data.get('phone')) == 7 or len(data.get('phone')) == 8):
            error["phone"] = 'error'
            error_message.append(
                _('Teléfono no válido. Por favor proporcione un teléfono válido.'))
        return error, error_message


class Quote(http.Controller):
    @http.route('/quote', auth='public', type='http', methods=['GET', 'POST'], website=True, sitemap=False)
    def quote(self, **kw):
        if request.httprequest.method == 'POST':
            upload = kw.get('upload', False)
            filename = upload.filename if upload else False
            file = upload.read() if upload else False

            errors = validator(kw)

            if upload and not file.startswith(b'%PDF-'):
                errors.append(
                    {'field': 'upload', 'error': 'Ingrese un archivo PDF válido.'})

            if len(errors) > 0:
                kw['error'] = errors
                return http.request.render('farmaoffers_design.quote', kw)

            quote = request.env['farmaoffers.quote'].create({
                'name': kw.get('name'),
                'lastname': kw.get('lastname'),
                'city': kw.get('city'),
                'address': kw.get('address'),
                'phone': kw.get('phone'),
                'email': kw.get('email'),
                'description': kw.get('description'),
            })

            if upload:
                request.env['ir.attachment'].sudo().create({
                    'name': filename,
                    'type': 'binary',
                    'datas': base64.encodebytes(file),
                    'res_model': 'farmaoffers.quote',
                    'res_id': quote.id,
                    'res_field': 'file',
                    'mimetype': 'application/x-pdf'
                })

            render_values = {
                'title': 'Gracias!',
                'body': quote.name + ' estaremos contáctandole muy pronto',
                'back_button_text': 'Volver al inicio',
                'back_url': '/'
            }
            return http.request.render('farmaoffers_design.thanks_page', render_values)

        return http.request.render('farmaoffers_design.quote')


class FarmaOffersContact(http.Controller):
    @http.route('/farmaoffers-contact', auth='public', type='http', methods=['GET', 'POST'], website=True, sitemap=False)
    def contactus(self, **kw):
        if request.httprequest.method == 'POST':

            errors = validator(kw)

            if len(errors) > 0:
                kw['error'] = errors
                return http.request.render('farmaoffers_design.contact_us', kw)

            try:
                contact = request.env['farmaoffers.contactus'].create({
                    'name': kw.get('name'),
                    'lastname': kw.get('lastname'),
                    'company': kw.get('company'),
                    'email': kw.get('email'),
                    'message': kw.get('message')
                })
                render_values = {
                    'title': 'Gracias!',
                    'body': contact.name + ' estaremos contáctandole muy pronto',
                    'back_button_text': 'Volver al inicio',
                    'back_url': '/'
                }
                return http.request.render('farmaoffers_design.thanks_page', render_values)
            except:
                kw["error"] = "Ha ocurrido un error."
                return http.request.render('farmaoffers_design.contact_us', kw)

        return http.request.render('farmaoffers_design.contact_us')


class Prescription(http.Controller):
    @http.route('/prescription', auth='public', type='http', methods=['GET', 'POST'], website=True, sitemap=False)
    def prescription(self, **kw):
        if request.httprequest.method == 'POST':

            upload = kw.get('upload', False)
            filename = upload.filename if upload else False
            file = upload.read() if upload else False

            errors = validator(kw)

            if upload and not file.startswith(b'%PDF-'):
                errors.append(
                    {'field': 'upload', 'error': 'Ingrese un archivo PDF válido.'})

            if len(errors) > 0:
                kw['error'] = errors
                return http.request.render('farmaoffers_design.prescription', kw)

            prescription = request.env['farmaoffers.prescription'].create({
                'name': kw.get('name'),
                'lastname': kw.get('lastname'),
                'city': kw.get('city'),
                'address': kw.get('address'),
                'phone': kw.get('phone'),
                'email': kw.get('email'),
                'message': kw.get('message')
            })

            if upload:
                request.env['ir.attachment'].sudo().create({
                    'name': filename,
                    'type': 'binary',
                    'datas': base64.encodebytes(file),
                    'res_model': 'farmaoffers.prescription',
                    'res_id': prescription.id,
                    'res_field': 'file',
                    'mimetype': 'application/x-pdf'
                })

            render_values = {
                'title': 'Gracias!',
                'body': prescription.name + ' estaremos contáctandole muy pronto',
                'back_button_text': 'Volver al inicio',
                'back_url': '/'
            }
            return http.request.render('farmaoffers_design.thanks_page', render_values)

        return http.request.render('farmaoffers_design.prescription')


class AllOffers(http.Controller):
    @http.route('/all-offers', auth='public', type='http', methods=['GET'], website=True, sitemap=False)
    def allOffers(self, **kw):
        return http.request.render('farmaoffers_design.all_offers')


def validator(data, onlypaswords=False):
    errors = []
    for key in data.keys():
        if not onlypaswords and (key == 'name' or key == 'lastname'):
            if len(data[key]) < 5:
                errors.append(
                    {'field': key, 'error': f'El campo {key} debe tener más de 4 caracteres.'})
            if not re.match(r'[a-zA-Z +\s]+$', data[key]):
                errors.append(
                    {'field': key, 'error': f'El campo {key} debe contener solo letras.'})

        if not onlypaswords and (key == 'email' or key == 'login'):
            if not (re.fullmatch(regexEmail, data[key])):
                errors.append(
                    {'field': key, 'error': f'El campo {key} debe ser un correo válido.'})

        if not onlypaswords and (key == 'phone'):
            if not data[key].isdigit():
                errors.append(
                    {'field': key, 'error': f'El campo {key} debe ser śolo numéros.'})

            if len(data[key]) != 8 and len(data[key]) != 7:
                errors.append(
                    {'field': key, 'error': f'El campo {key} debe tener 7 u 8 dígitos.'})

        if key == 'password':
            SpecialSym = ['$', '@', '#', '%']
            val = True

            if len(data[key]) < 6:
                val = False

            if not any(char.isdigit() for char in data[key]):
                val = False

            if not any(char.isupper() for char in data[key]):
                val = False

            if not any(char.islower() for char in data[key]):
                val = False

            if not any(char in SpecialSym for char in data[key]):
                val = False
            if not val:
                errors.append(
                    {'field': key, 'error': f'La contraseña debe contener 6 o más dígitos, debe contener al menos 1 mayúscula, 1 minúscula, 1 número y 1 símbolo ($, @, #, %).'})

    return errors
