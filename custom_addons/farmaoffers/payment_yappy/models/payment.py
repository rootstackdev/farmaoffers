# coding: utf-8

import json
import chardet
import os
from werkzeug import urls
from cryptography.fernet import Fernet

from odoo import api, fields, models, _
from odoo.tools.pycompat import to_text
from odoo.exceptions import ValidationError
from odoo.addons.payment_yappy.controllers.main import YappyController


class AcquirerPaypal(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[
        ('yappy', 'Yappy')
    ], ondelete={'yappy': 'set default'})
    yappy_merchant_id = fields.Char(
        'Merchant ID', required_if_provider='yappy', groups='base.group_user')
    yappy_secret_key = fields.Char(
        'Secret Key', required_if_provider='yappy', groups='base.group_user')

    @api.model
    def _get_yappy_urls(self):
        from subprocess import check_output
        global form_data

        # Encriptar referencia
        try:
            fernet = Fernet(YappyController._secret_key)
            encripted_reference = fernet.encrypt(form_data["reference"].encode()).decode()
        except Exception:
            raise

        # Armar payload
        data = {
            'environment': self.state,
            'merchant_id': self.yappy_merchant_id,
            'secret_key': self.yappy_secret_key,
            'payment': {
                'total': form_data['amount'],
                'subtotal': form_data['amount_untaxed'],
                'shipping': form_data['amount_delivery'],
                'discount': 0.00,
                'taxes': form_data['amount_tax'] or '0.00',
                'orderId': form_data['reference'],
                'successUrl': urls.url_join(self.get_base_url(),
                                            f'/payment/yappy/return?reference={encripted_reference}'),
                'failUrl': urls.url_join(self.get_base_url(),
                                         f'/payment/yappy/fail?fail=true&reference={encripted_reference}'),
                'tel': form_data['partner_phone'],
                'domain': self.get_base_url()
            }
        }

        # Ejecutar Node
        node_script = os.path.expanduser('~') + '/node_sdk/dist/index.js'
        try:
            content = check_output(['node', node_script, json.dumps(data)])
        except Exception:
            raise

        # Decodificar salida
        try:
            enc_info = chardet.detect(content) or {}
            encoding = (enc_info.get('encoding') or '').lower()
            content = content.decode(encoding).encode('utf-8')
        except Exception:
            raise

        # Parsear JSON
        try:
            response = json.loads(to_text(content))
        except Exception:
            raise

        # Evaluar respuesta
        if response['success']:
            return response['url']

        raise ValidationError(f"{response['error']['code']} - {response['error']['message']}")

    def yappy_form_generate_values(self, values):
        global form_data
        self.ensure_one()
        form_data = values
        return values

    def yappy_get_form_action_url(self):
        self.ensure_one()
        return self._get_yappy_urls()

    def get_form_action_url(self):
        self.ensure_one()
        return self.yappy_get_form_action_url()


class TxAdyen(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _yappy_form_get_tx_from_data(self, data):
        fernet = Fernet(YappyController._secret_key)
        reference = fernet.decrypt(data.get('reference').encode()).decode()
        transaction = self.search([('reference', '=', reference)])
        return transaction

    def _yappy_form_validate(self, data):
        if (data.get('fail') == 'true'):
            error = 'No se pudo procesar el pago con Yappy'
            self._set_transaction_error(error)
            return self.write({
                'state_message': error
            })
        else:
            self._set_transaction_done()
        return True