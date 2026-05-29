import json
import unicodedata
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class FarmaoffersThemeCheckout(http.Controller):

    @http.route('/fo/branches', type='http', auth='public', website=True, csrf=False)
    def fo_branches(self, **kw):
        branches = request.env['multi.branch'].sudo().search([], order='name')
        branches = branches.filtered(
            lambda branch: 'chitr' not in unicodedata.normalize(
                'NFKD', branch.name or ''
            ).encode('ascii', 'ignore').decode('ascii').lower()
        )
        payload = [{'id': b.id, 'name': b.name} for b in branches]
        return request.make_response(
            json.dumps(payload),
            headers=[('Content-Type', 'application/json; charset=utf-8')]
        )


class FarmaoffersWebsiteSale(WebsiteSale):

    def _get_mandatory_address_fields(self, country_sudo):
        field_names = super()._get_mandatory_address_fields(country_sudo)
        if country_sudo.state_ids:
            field_names.add('state_id')
        return field_names

    def _check_shipping_method(self, order_sudo):
        """En modo branch no se requiere método de envío."""
        if order_sudo and order_sudo.shipping_mode == 'branch':
            return None  # sin redirección, dejar pasar
        return super()._check_shipping_method(order_sudo)

    @http.route()
    def shop_checkout(self, try_skip_step=None, **query_params):
        order = request.website.sale_get_order()
        response = super().shop_checkout(try_skip_step=try_skip_step, **query_params)

        if order and order.shipping_mode == 'branch':
            order.sudo().write({'carrier_id': False})
            order.sudo()._remove_delivery_line()

        return response

    @http.route()
    def shop_confirm_order(self, **post):
        order = request.website.sale_get_order()

        if order and order.shipping_mode == 'branch':
            order.sudo().write({'carrier_id': False})
            order.sudo()._remove_delivery_line()
            return request.redirect('/shop/payment')

        return super().shop_confirm_order(**post)


class FarmaoffersCheckoutShipping(http.Controller):

    @http.route('/fo/checkout/set_shipping', type='http', auth='public', website=True, csrf=False, methods=['POST'])
    def fo_set_shipping(self, **kw):
        order = request.website.sale_get_order()
        if not order:
            return request.make_response(
                json.dumps({'ok': False, 'error': 'no_order'}),
                headers=[('Content-Type', 'application/json; charset=utf-8')]
            )

        try:
            data = json.loads(request.httprequest.data.decode('utf-8') or '{}')
        except Exception:
            data = {}

        pickup = bool(data.get('pickup'))
        branch_id = data.get('branch_id')

        if pickup:
            order.sudo().write({
                'shipping_mode': 'branch',
                'branch_id': int(branch_id) if branch_id else False,
                'carrier_id': False,
            })
            order.sudo()._remove_delivery_line()

            return request.make_response(
                json.dumps({'ok': True, 'mode': 'branch'}),
                headers=[('Content-Type', 'application/json; charset=utf-8')]
            )

        order.sudo().write({
            'shipping_mode': 'address',
            'branch_id': False,
        })

        return request.make_response(
            json.dumps({'ok': True, 'mode': 'address'}),
            headers=[('Content-Type', 'application/json; charset=utf-8')]
        )


class FarmaoffersHomepage(http.Controller):

    @http.route("/", type="http", auth="public", website=True, sitemap=False)
    def farmaoffers_root_home(self, **kw):
        return request.render("website.farmaoffers_homepage", {})


class FarmaoffersAllOffers(http.Controller):

    @http.route('/all-offers', auth='public', type='http', methods=['GET'], website=True, sitemap=False)
    def allOffers(self, **kw):
        return http.request.render('farmaoffers_theme.all-offers')
    
class FarmaoffersCartHeaderController(http.Controller):

    @http.route('/shop/cart/header_info', type='json', auth='public', website=True)
    def cart_header_info(self):
        order = request.website.sale_get_order()

        if not order:
            currency = request.website.currency_id
            return {
                'quantity': 0,
                'amount_total': 0.0,
                'amount_total_formatted': f'{currency.symbol} 0.00',
            }

        currency = order.pricelist_id.currency_id or request.website.currency_id

        return {
            'quantity': order.cart_quantity,
            'amount_total': order.amount_total,
            'amount_total_formatted': f'{currency.symbol} {order.amount_total:.2f}',
        }
