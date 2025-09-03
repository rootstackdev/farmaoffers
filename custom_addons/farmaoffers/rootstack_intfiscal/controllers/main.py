import base64

from odoo import http
from odoo.http import request, content_disposition
from werkzeug.exceptions import NotFound


class MainController(http.Controller):
    @http.route('/ebi_client/download_invoice', auth='user')
    def download_invoice(self, **kw):
        if kw['format'] == 'xml':
            function_name = 'descargaXml'
            file_extension = '.xml'
            content_type = 'text/xml'
        elif kw['format'] == 'pdf':
            function_name = 'descargaPdf'
            file_extension = '.pdf'
            content_type = 'application/pdf'
        else:
            return NotFound()
        company = request.env.company
        ebi_client = company.get_ebi_client()
        res = getattr(ebi_client, function_name)(kw['codigo_sucursal_emisor'], kw['number'],
                                                 kw['serie'], kw['tipo_documento'], kw['tipo_emision'])
        content_base64 = base64.b64decode(res['documento'])
        headers = [('Content-Disposition', content_disposition(kw["serie"] + kw["number"] + file_extension)),
                   ('Content-Length', len(content_base64)), ('Content-Type', content_type)]
        response = request.make_response(content_base64, headers)
        return response
