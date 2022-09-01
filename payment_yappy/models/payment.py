# coding: utf-8

import logging
import json
import chardet
from werkzeug import urls
from os.path import dirname

from odoo import api, fields, models, _
from odoo.tools.pycompat import to_text
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AcquirerPaypal(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[
        ('yappy', 'Yappy')
    ], ondelete={'yappy': 'set default'})
    yappy_merchant_id = fields.Char('Merchant ID', required_if_provider='yappy', groups='base.group_user')
    yappy_secret_key = fields.Char('Secret Key', required_if_provider='yappy', groups='base.group_user')

    @api.model
    def _get_yappy_urls(self):
        from subprocess import check_output
        global form_data
        data = {
            'environment': self.state,
            'merchant_id': self.yappy_merchant_id,
            'secret_key': self.yappy_secret_key,
            'payment': {
                'total': form_data['amount'],
                'subtotal': form_data['amount_untaxed'],
                'shipping': 0.00,
                'discount': 0.00,
                'taxes': form_data['amount_tax'],
                'orderId': form_data['reference'],
                'successUrl': urls.url_join(self.get_base_url(), '/shop/confirmation'),
                'failUrl': urls.url_join(self.get_base_url(), '/shop/fail'),
                'tel': form_data['partner_phone'],
                'domain': self.get_base_url()
            }
        }
        _logger.info("DATA PARA GENERAR EL LINK DE YAPPY", json.dumps(data))
        content = check_output(['node', dirname(__file__)+'/node_sdk/dist/index.js', json.dumps(data)])
        encoding = chardet.detect(content)['encoding'].lower()
        content = content.decode(encoding).encode('utf-8')
        response = json.loads(to_text(content))
        _logger.info(response)
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
