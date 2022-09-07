import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class YappyController(http.Controller):
    _secret_key = '5cKurIO61GWtpjhmhdoHjxC7gEbODGBx7rNzqqEUDfo='

    @http.route([
        '/payment/yappy/return',
        '/payment/yappy/fail'
    ], type='http', auth='public', csrf=False)
    def yappy_return(self, **post):
        _logger.info('Beginning Yappy form_feedback with post data %s',
                     pprint.pformat(post))  # debug
        request.env['payment.transaction'].sudo().form_feedback(post, 'yappy')
        return werkzeug.utils.redirect('/payment/process')
