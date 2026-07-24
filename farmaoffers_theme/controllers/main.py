import json
import re
import unicodedata
from odoo import _, http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


# Corregimientos of the Distrito de Panamá (Ciudad de Panamá), plus common aliases
# used by customers when filling in the "city" field of their delivery address.
PANAMA_CITY_LOCALITIES = frozenset({
    'panama', 'panama city', 'ciudad de panama', 'distrito de panama',
    '24 de diciembre', 'alcalde diaz', 'ancon', 'bella vista', 'betania',
    'bethania', 'caimitillo', 'calidonia', 'la exposicion', 'chilibre',
    'curundu', 'don bosco', 'el chorrillo', 'ernesto cordoba campos',
    'juan diaz', 'las cumbres', 'las garzas', 'las mananitas', 'pacora',
    'parque lefevre', 'pedregal', 'pueblo nuevo', 'rio abajo', 'san felipe',
    'san francisco', 'san martin', 'santa ana', 'tocumen',
})
PANAMA_PROVINCE_NAMES = frozenset({'panama', 'provincia de panama'})


def _normalize_text(value):
    if not value:
        return ''
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    return value.strip().lower()


def _locality_candidates(city):
    """Yield the normalized city plus each of its comma/slash/dash-separated segments.

    Lets "Panama, Panama" or "Panama City, Panama" match on a segment (e.g. "panama")
    without falling back to raw substring search, which could false-match an unrelated
    locality that merely contains one of our allowed words (e.g. "Panamania").
    """
    normalized = _normalize_text(city)
    if not normalized:
        return
    yield normalized
    for segment in re.split(r'[,/-]+', normalized):
        segment = segment.strip()
        if segment:
            yield segment


def is_panama_city_address(country, state, city):
    """Whether the given country/state/city correspond to Ciudad de Panamá."""
    if not country or country.code != 'PA':
        return False
    if state and _normalize_text(state.name) not in PANAMA_PROVINCE_NAMES:
        return False
    return any(candidate in PANAMA_CITY_LOCALITIES for candidate in _locality_candidates(city))


def _panama_geo_restriction_applies(order_sudo, address_type, use_delivery_as_billing):
    """Whether the Ciudad de Panamá restriction applies to this address submission.

    It applies to delivery addresses (or billing addresses used as delivery), except
    when the order is in "Retirar en sucursal" (pickup) mode.
    """
    is_pickup_order = bool(order_sudo and order_sudo.shipping_mode == 'branch')
    applies_to_delivery = (
        address_type == 'delivery' or (address_type == 'billing' and use_delivery_as_billing)
    )
    return applies_to_delivery and not is_pickup_order


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

    def _check_delivery_address(self, partner_sudo):
        """Bloquear direcciones de entrega fuera de Ciudad de Panamá.

        No aplica cuando el pedido está en modo "Retirar en sucursal", ya que en
        ese caso no se realiza ningún envío a la dirección del cliente.
        """
        if not super()._check_delivery_address(partner_sudo):
            return False

        order_sudo = request.website.sale_get_order()
        if order_sudo and order_sudo.shipping_mode == 'branch':
            return True

        return is_panama_city_address(
            partner_sudo.country_id, partner_sudo.state_id, partner_sudo.city
        )

    def _validate_address_values(
        self, address_values, partner_sudo, address_type, use_delivery_as_billing,
        required_fields, is_main_address, **kwargs
    ):
        invalid_fields, missing_fields, error_messages = super()._validate_address_values(
            address_values, partner_sudo, address_type, use_delivery_as_billing,
            required_fields, is_main_address, **kwargs
        )

        order_sudo = request.website.sale_get_order()

        if _panama_geo_restriction_applies(order_sudo, address_type, use_delivery_as_billing):
            country_id = address_values.get('country_id', partner_sudo.country_id.id)
            state_id = address_values.get('state_id', partner_sudo.state_id.id)
            city = address_values.get('city', partner_sudo.city)

            country = request.env['res.country'].browse(country_id) if country_id else None
            state = request.env['res.country.state'].browse(state_id) if state_id else None

            if not is_panama_city_address(country, state, city):
                invalid_fields.add('city')
                error_messages.append(_(
                    "Por el momento solo realizamos entregas a domicilio dentro de Ciudad de"
                    " Panamá. Verifica el país, la provincia y la ciudad de tu dirección, o"
                    " continúa y elige \"Retirar en sucursal\" en el siguiente paso."
                ))

        return invalid_fields, missing_fields, error_messages

    def _prepare_address_form_values(
        self, order_sudo, partner_sudo, address_type, use_delivery_as_billing, callback='', **kwargs
    ):
        values = super()._prepare_address_form_values(
            order_sudo, partner_sudo, address_type, use_delivery_as_billing, callback=callback,
            **kwargs
        )

        if _panama_geo_restriction_applies(order_sudo, address_type, use_delivery_as_billing):
            panama = request.env['res.country'].search([('code', '=', 'PA')], limit=1)
            if panama:
                values['countries'] = panama
                if values.get('country') != panama:
                    values['country'] = panama
                    values['country_states'] = panama.state_ids
                    values['state_id'] = False

        return values

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
