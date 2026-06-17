# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

import json
import logging
from odoo import _, http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.exceptions import ValidationError
from odoo.http import request
from suds.client import Client
from suds.sudsobject import asdict
from suds.wsse import Security, UsernameToken

_logger = logging.getLogger(__name__)

PANAMA_COUNTRY_CODE = 'PA'

reason_code = {
    100: 'Successful transaction',
    101: 'The request is missing one or more required fields',
    102: 'One or more fields in the request contains invalid data',
    104: 'The merchantReferenceCode sent with this authorization request matches the merchantReferenceCode of another authorization request that you sent in the last 15 minutes.',
    150: 'Error: General system failure',
    151: 'Error: The request was received but there was a server timeout. This error does not include timeouts between the client and the server.',
    152: 'Error: The request was received, but a service did not finish running in time',
    201: 'The issuing bank has questions about the request. You do not receive an authorization code in the reply message, but you might receive one verbally by calling the processor',
    202: 'Expired card. You might also receive this if the expiration date you provided does not match the date the issuing bank has on file',
    203: 'General decline of the card. No other information provided by the issuing bank',
    204: 'Insufficient funds in the account',
    205: 'Stolen or lost card',
    207: 'Issuing bank unavailable',
    208: 'Inactive card or card not authorized for card-not-present transactions',
    210: 'The card has reached the credit limit',
    211: 'Invalid card verification number',
    221: 'The customer matched an entry on the processor\'s negative file',
    231: 'Invalid account number',
    232: 'The card type is not accepted by the payment processor',
    233: 'General decline by the processor',
    234: 'There is a problem with your CyberSource merchant configuration',
    235: 'The requested amount exceeds the originally authorized amount. Occurs, for example, if you try to capture an amount larger than the original authorization amount. This reason code only applies if you are processing a capture through the API',
    236: 'Processor Failure',
    238: 'The authorization has already been captured. This reason code only applies if you are processing a capture through the API',
    239: 'The requested transaction amount must match the previous transaction amount. This reason code only applies if you are processing a capture or credit through the API',
    240: 'The card type sent is invalid or does not correlate with the credit card number',
    241: 'The request ID is invalid. This reason code only applies when you are processing a capture or credit through the API',
    242: 'You requested a capture through the API, but there is no corresponding, unused authorization record. Occurs if there was not a previously successful authorization request or if the previously successful authorization has already been used by another capture request. This reason code only applies when you are processing a capture through the API',
    243: 'The transaction has already been settled or reversed',
    246: 'The capture or credit is not voidable because the capture or credit information has already been submitted to your processor. Or, you requested a void for type a of transaction that cannot be voided. This reason code applies only if you are processing a void through the API',
    247: 'You requested a credit for a capture that was previously voided. This reason code applies only if you are processing a void through the API',
    250: 'Error: The request was received, but there was a timeout at the payment processor',
    480: 'The order is marked for review by Decision Manager',
    481: 'The order was rejected by Decision Manager',
    520: 'The authorization request was approved by the issuing bank but declined by CyberSource based on your Smart Authorization settings',
    400: 'Soft Decline - Fraud score exceeds threshold.'
}


class InheritWebsiteSale(WebsiteSale):

    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        response = super(InheritWebsiteSale, self).shop(page=page, category=category, search=search, ppg=ppg, **post)
        payment_provider = request.env['payment.provider'].sudo().search([('code', '=', 'cybersource')])
        payment_token = request.env['payment.token'].sudo().search([('provider_id', '=', payment_provider.id)])
        if not payment_provider.allow_tokenization:
            for token_id in payment_token:
                token_id.unlink()
        if post.get('error'):
            return request.render('aspl_payment_cybersource_ee.PaymentFailed', {'reason': request.session.get('reason')})
        return response


class CyberSourceController(http.Controller):

    def recursive_dict(self, d):
        out = {}
        for k, v in asdict(d).items():
            if hasattr(v, '__keylist__'):
                out[k] = self.recursive_dict(v)
            elif isinstance(v, list):
                out[k] = []
                for item in v:
                    if hasattr(item, '__keylist__'):
                        out[k].append(self.recursive_dict(item))
                    else:
                        out[k].append(item)
            else:
                out[k] = v
        return out

    @http.route(['/payment/cybersource/s2s/create_json_3ds'], type='json', auth='public', csrf=False)
    def cybersource_s2s_create_json_3ds(self, verify_validity=False, **kwargs):
        """
        :param verify_validity: False
        :param kwargs: all card and order details
        :return: Dict after successfully payment
        """
        post = kwargs.get('processingValues', {})
        if post.get('cc_number') and post.get('cc_holder_name') and post.get('cc_expiry') and post.get('cc_cvc'):
            payment_provider = request.env['payment.provider'].sudo().search(
                [('id', '=', post.get('provider_id')), ('code', '=', 'cybersource')],
                limit=1,
            )
            tx = request.env['payment.transaction'].sudo().search(
                [
                    ('reference', '=', post.get('reference')),
                    ('provider_id', '=', payment_provider.id),
                    ('provider_code', '=', 'cybersource'),
                ],
                limit=1,
            )
            if not payment_provider or not tx:
                raise ValidationError(_("No se encontró una transacción válida de CyberSource."))

            self._validate_transaction_country(tx)
            response_data = self.request_payment_status(post, tx, payment_provider)
            if not response_data:
                raise ValidationError(
                    _("CyberSource no devolvió una respuesta para la transacción.")
                )

            data = json.loads(json.dumps(self.recursive_dict(response_data)))
            code = data.get('reasonCode')
            try:
                code = int(code)
            except (TypeError, ValueError):
                pass
            reason = reason_code.get(code, 'Error de pago (código: {})'.format(code))
            data.update({'amount': tx.amount, 'id': tx.reference, 'reason': reason})
            request.session['reason'] = reason
            request_id = data.get('requestID')
            request.session['requestID'] = request_id
            transaction = request.env['payment.transaction'].sudo()._handle_notification_data(
                'cybersource',
                {
                    'reference': tx.reference,
                    'reason_code': code,
                    'request_id': request_id,
                    'reason': reason,
                },
            )

            token = request.env['payment.token']
            if (
                code == 100
                and tx.tokenize
                and payment_provider.allow_tokenization
            ):
                token = request.env['payment.token'].sudo().create({
                    'partner_id': tx.partner_id.id,
                    'provider_id': payment_provider.id,
                    'provider_ref': request_id or tx.reference,
                    'active': True,
                    'payment_method_id': tx.payment_method_id.id,
                    'payment_details': 'XXXXXXXXXXXX%s - %s' % (
                        post.get('cc_number')[-4:],
                        post.get('cc_holder_name'),
                    ),
                })
                transaction.token_id = token.id

            return {
                'result': code == 100,
                '3d_secure': False,
                'id': token.id if token else False,
                'short_name': token.provider_ref if token else False,
                'verified': code == 100,
                'state': transaction.state,
                'reason': reason,
            }

        else:
            raise ValidationError(_("Ingrese datos de tarjeta válidos."))

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True)
    def payment_confirmation(self, **post):
        '''
        :param post: Not in use
        :return: Redirect or render accordingly
        '''
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            if not order or order.state != 'draft':
                request.website.sale_reset()
            return request.render("website_sale.confirmation", {'website_sale_order': order,'order':order})
        else:
            return request.redirect('/shop')

    def _validate_transaction_country(self, tx):
        order = tx.sale_order_ids[:1]
        shipping_partner = order.partner_shipping_id if order else tx.partner_id
        if shipping_partner.country_id.code != PANAMA_COUNTRY_CODE:
            raise ValidationError(
                _("CyberSource solo está disponible para pedidos con entrega en Panamá.")
            )

    def request_payment_status(self, post, tx, payment_provider):
        '''
        Method checks card details and create response from cybersource
        :param post: Dict of order and card details
        :return: response from the cybersource
        '''
        if payment_provider.state == 'enabled':
            # Production link for India
            # https://ics2wsa.in.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.191.wsdl
            wsdl = 'https://ics2wsa.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.205.wsdl'
        else:
            wsdl = 'https://ics2wstesta.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.205.wsdl'
        transaction_security_key = payment_provider.cybersource_key
        merchant_id = payment_provider.cybersource_merchant_id
        self.merchant_id = merchant_id
        self.client = Client(wsdl)
        security = Security()
        token = UsernameToken(self.merchant_id, transaction_security_key)
        security.tokens.append(token)
        self.client.set_options(wsse=security)
        data = {}
        data['merchantID'] = self.merchant_id
        data['merchantReferenceCode'] = tx.reference
        data['purchaseTotals'] = self.client.factory.create('ns0:PurchaseTotals')
        data['purchaseTotals'].currency = tx.currency_id.name
        data['purchaseTotals'].grandTotalAmount = tx.amount
        data['pos'] = self.client.factory.create('ns0:pos')

        order = tx.sale_order_ids[:1]
        billing_partner = order.partner_invoice_id if order else tx.partner_id
        shipping_partner = order.partner_shipping_id if order else tx.partner_id

        data['billTo'] = self.client.factory.create('ns0:BillTo')
        data['billTo'].email = billing_partner.email
        data['billTo'].firstName = billing_partner.name
        data['billTo'].lastName = billing_partner.name
        data['billTo'].street1 = billing_partner.street
        data['billTo'].street2 = billing_partner.street2 or None
        data['billTo'].city = billing_partner.city
        data['billTo'].state = billing_partner.state_id.code or None
        data['billTo'].postalCode = billing_partner.zip
        data['billTo'].country = billing_partner.country_id.code
        if request.httprequest.remote_addr:
            data['billTo'].ipAddress = request.httprequest.remote_addr

        data['shipTo'] = self.client.factory.create('ns0:shipTo')
        data['shipTo'].firstName = shipping_partner.name
        data['shipTo'].lastName = shipping_partner.name
        data['shipTo'].street1 = shipping_partner.street
        data['shipTo'].street2 = shipping_partner.street2 or None
        data['shipTo'].city = shipping_partner.city
        data['shipTo'].state = shipping_partner.state_id.code or None
        data['shipTo'].country = shipping_partner.country_id.code
        data['shipTo'].postalCode = shipping_partner.zip
        data['apPaymentType'] = 'EPS'
        data['card'] = self.client.factory.create('ns0:Card')
        data['card'].accountNumber = int(post.get('cc_number'))
        data['card'].expirationMonth = int(post.get('cc_expiry')[:2])
        data['card'].expirationYear = int('20' + post.get('cc_expiry')[3:])
        data['card'].cvNumber = post.get('cc_cvc')
        data['ccAuthService'] = self.client.factory.create('ns0:ccAuthService')
        data['ccAuthService']._run = 'true'
        data['ccCaptureService'] = self.client.factory.create('ns0:ccCaptureService')
        data['ccCaptureService']._run = 'true'
        try:
            resp = self.client.service.runTransaction(**data)
        except Exception:
            _logger.exception(
                "CyberSource request failed for transaction %s",
                tx.reference,
            )
            resp = None
        return resp

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
