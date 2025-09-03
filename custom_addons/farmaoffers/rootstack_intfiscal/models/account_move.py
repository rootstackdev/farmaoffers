import json
import threading
import requests
import logging
from odoo import api, fields, models, _, tools
from odoo.tools import float_repr
from odoo.exceptions import ValidationError
from odoo.addons.rootstack_intfiscal.util import convert_dict_to_list_of_tuplas, get_key_of_value
from rootstack_ebi.catalog import TIPO_EMISION, NATURALEZA_OPERACION, TIPO_OPERACION, FORMATO_CAFE, ENTREGA_CAFE, \
    ENVIO_CONTENEDOR, TIPO_VENTA, TASA_ITBMS
from rootstack_ebi.document import Client, TransactionData, Item, Totals, FormaPago, ElectronicDocument, \
    DocFiscalReferenciado, convert_to_dict, DatosFacturaExportacion, DescuentoBonificacion

_logger = logging.getLogger(__name__)


lock_send_einvoice = threading.Lock()


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _default_values(self, dict_Values):
        out_invoice = self.env.context.get('default_move_type', None)
        if out_invoice in ('out_invoice', 'out_refund'):
            return list(dict_Values.keys())[0]
        return None

    # Fields for electronic invoice
    ei_emission_type = fields.Selection(convert_dict_to_list_of_tuplas(TIPO_EMISION), string='Emission Type',
                                        default=lambda self: self._default_values(TIPO_EMISION))
    ei_nature_operation = fields.Selection(convert_dict_to_list_of_tuplas(NATURALEZA_OPERACION),
                                           string='Nature of the Operation',
                                           default=lambda self: self._default_values(NATURALEZA_OPERACION))
    ei_sale_type = fields.Selection(convert_dict_to_list_of_tuplas(TIPO_VENTA), string='Type of Sale',
                                    default=lambda self: self._default_values(TIPO_VENTA))
    ei_operation_type = fields.Selection(convert_dict_to_list_of_tuplas(TIPO_OPERACION), string='Type of Operation',
                                         default=lambda self: self._default_values(TIPO_OPERACION))
    ei_format_cafe = fields.Selection(convert_dict_to_list_of_tuplas(FORMATO_CAFE), string='CAFE Format',
                                      default=lambda self: self._default_values(FORMATO_CAFE))
    ei_delivery_cafe = fields.Selection(convert_dict_to_list_of_tuplas(ENTREGA_CAFE), string='CAFE Delivery',
                                        default=lambda self: self._default_values(ENTREGA_CAFE))
    ei_container_shipping = fields.Selection(convert_dict_to_list_of_tuplas(ENVIO_CONTENEDOR),
                                             string='Container Shipping',
                                             default=lambda self: self._default_values(ENVIO_CONTENEDOR))
    ei_operation_destination = fields.Selection([('1', 'Panamá'), ('2', 'Extranjero')],
                                                string='Destination of Operation', default='1')
    status_fe = fields.Selection([
        ('01', 'Not Sent'),
        ('02', 'Sent'),
        ('03', 'Authorized'),
        ('04', 'Canceled')
    ], readonly=True, default='01', copy=False)
    cufe_electronic_invoice = fields.Char(
        string='CUFE', readonly=True, copy=False)
    is_electronic_invoice = fields.Boolean(
        compute='_compute_is_electronic_invoice')
    allow_fiscal_print = fields.Boolean(
        compute='_compute_is_electronic_invoice')
    ei_qr = fields.Char(string='QR Code', readonly=True, copy=False)
    ei_document_number = fields.Char('Document number', copy=False)
    ei_document_serie = fields.Char('Document Serie', copy=False)

    @api.depends('move_type', 'journal_id')
    def _compute_is_electronic_invoice(self):
        for item in self:
            item.is_electronic_invoice = False
            item.allow_fiscal_print = False
            if item.move_type in (
                    'out_invoice',
                    'out_refund') and item.journal_id.ei_document_type and item.env.company.invoicing_mode in (
                    '02', '03') and item.journal_id.ei_document_type:
                item.is_electronic_invoice = True
            if item.move_type in ('out_invoice', 'out_refund') and item.env.company.invoicing_mode in ('01', '03'):
                item.allow_fiscal_print = True

    def get_data_printer(self, _printer_info):
        """ Check format of printer ( conection_port:printer_model ) """
        data_printer = _printer_info.split(":")
        if len(data_printer) == 2:
            return data_printer
        return False

    def intfiscal_print(self):
        url = self.env['ir.config_parameter'].sudo().get_param('intfiscal_url')
        token = self.env['ir.config_parameter'].sudo(
        ).get_param('intfiscal_token')
        default_printer = self.env['ir.config_parameter'].sudo(
        ).get_param('intfiscal_default_printer')
        invoice_body = self._prepare_data_to_intfiscal()
        context = {
            'url': url,
            'token': token,
            'dialog_size': 'medium',
            'invoice_body': invoice_body,
            'default_printer': default_printer
        }
        return {
            'type': 'ir.actions.client',
            'name': 'Impresion fiscal',
            'tag': 'rootstack_intfiscal.fiscal_printer',
            'target': 'new',
            'context': context
        }

    def send_to_intfiscal(self, connection_port, printer_model):
        url = self.env['ir.config_parameter'].sudo().get_param('intfiscal_url')
        token = self.env['ir.config_parameter'].sudo(
        ).get_param('intfiscal_token')
        body = self._prepare_data_to_intfiscal()
        params = {
            'connection_port': connection_port,
            'printer_model': printer_model,
            'token': token
        }
        try:
            requests.post(url='%s/printer/v2' %
                          url, data=json.dumps(body), params=params)
        except:
            raise ValidationError("Error al enviar la impresión")

    def _prepare_data_to_intfiscal(self):
        if not self.company_id.ruc:
            raise ValidationError(
                _("you need to set the ruc field in the company configuration"))
        if not self.company_id.dv.name:
            raise ValidationError(
                _("you need to set the dv field in the company configuration"))
        # Fill header
        vals = {
            'clientRuc': getattr(self.partner_id, self.company_id.ruc.name),
            'clientSocialReason': self.partner_id.name,
            'dv': getattr(self.partner_id, self.company_id.dv.name),
            'tax': self.amount_tax,
            'clientDetails': [],
            'items': []
        }

        # detect credit note
        if self.move_type == 'out_refund':
            vals["creditNoteRelatedInvoice"] = self.reversed_entry_id.name

        # Fill items
        for line in self.line_ids.filtered(lambda x: not x.exclude_from_invoice_tab and x.price_subtotal >= 0):
            data_tax = line.tax_ids.compute_all(
                line.price_unit, self.currency_id, line.quantity)
            currency_id = self.currency_id
            tax_total = 0
            for item in data_tax["taxes"]:
                tax_total += item["amount"]
            tax_total = tools.float_repr(tax_total, currency_id.decimal_places)
            vals_line = {
                'code': line.product_id.default_code,
                'name': line.name,
                'tax': tax_total,
                'value': line.price_subtotal,
                'qty': line.quantity,
                'comments': []
            }
            vals['items'].append(vals_line)

        # Find negative values that will be global discount
        """ vals['listaDescBonificacion'] = []
        for line in self.line_ids.filtered(lambda x: not x.exclude_from_invoice_tab and x.price_subtotal <= 0):
            vals['listaDescBonificacion'].append({
                ''
            }) """

        # Fill client details
        partner_id = self.partner_id
        partner_id.name and vals["clientDetails"].append(partner_id.name)
        partner_id.street and vals["clientDetails"].append(partner_id.street)
        partner_id.city and vals["clientDetails"].append(partner_id.city)
        partner_id.state_id and vals["clientDetails"].append(
            partner_id.state_id.display_name)
        partner_id.country_id and vals["clientDetails"].append(
            partner_id.country_id.display_name)
        partner_id.phone and vals["clientDetails"].append(partner_id.phone)
        return vals

    def action_send_electronic_invoice(self):
        """ Generate the electronic receipt and send it """

        with lock_send_einvoice:
            sequence_id = self.journal_id.sequence_id
            serie, number = self.get_sequence_edocument(sequence_id)
            self.ei_document_serie = serie
            self.ei_document_number = number
            edocument = ElectronicDocument()
            client = self.format_client_values()
            transaction = self.format_transaction_data()
            transaction.cliente = client
            if (self.move_type == 'out_refund' and self.reversed_entry_id) or self.debit_origin_id:
                """ Check if the document is a credit note or debit note"""
                listaDocsFiscalReferenciados = self.get_list_docs_referenced()
                transaction.listaDocsFiscalReferenciados = listaDocsFiscalReferenciados
            if self.journal_id.ei_document_type == '03':
                invoice_export_data = self.format_invoice_export_data()
                transaction.datosFacturaExportacion = invoice_export_data
            edocument.datosTransaccion = transaction
            items_list = self.format_items_data()
            edocument.listaItems = items_list
            totals = self.format_totals_data(items_data=items_list)
            payment = self.format_payment_data()
            totals.listaFormaPago = []
            totals.listaFormaPago.append(payment)
            edocument.totalesSubTotales = totals
            edocument.tipoSucursal = self.journal_id.ei_branch_type
            edocument.codigoSucursalEmisor = self.journal_id.ei_branch_code
            response = self.send_edocument_to_webservice(edocument)
            sequence_id._next_do()
            self.env.cr.commit()
            return response

    def get_sequence_edocument(self, sequence_id):
        sequence = sequence_id.get_next_char(
            sequence_id.number_next_actual)
        if len(sequence) != 13:
            raise ValidationError(
                _('the invoice number is not in the correct format'))
        serie = sequence[0:3]
        number = sequence[3:]
        return serie, number

    def send_edocument_to_webservice(self, edocument):
        ebi_client = self.env.company.get_ebi_client()
        res = ebi_client.enviar(edocument)
        if res['codigo'] == '200':
            self.status_fe = '02'
            self.cufe_electronic_invoice = res['cufe']
            self.ei_qr = res['qr']
            return self.show_message()
        else:
            raise ValidationError(res['mensaje'])

    def show_message(self):
        msg = f"""
            <div class="alert alert-light align-items-center d-flex justify-content-center m-0" role="alert">
                <span class="fa fa-2x fa-check-circle mr-2 text-primary"/> La factura electrónica &nbsp;<strong>{self.ei_document_serie}{self.ei_document_number}</strong>&nbsp; fue generada correctamente
            </div>
        """
        if self.partner_id.email:
            msg += f"""
                <div class="alert alert-light align-items-center d-flex justify-content-center m-0" role="alert">
                    <span class="fa fa-2x fa-check-circle mr-2 text-primary"/> La factura electrónica fue enviada al correo &nbsp;<strong>{self.partner_id.email}</strong>
                </div>
            """
        return {
            'type': 'ir.actions.client',
            'name': 'Operación Exitosa',
            'tag': 'rootstack_intfiscal.message',
            'target': 'new',
            'context': {
                'message': msg
            }
        }

    def get_list_docs_referenced(self):
        listaDocsFiscalReferenciados = []
        doc_referenced = DocFiscalReferenciado()
        move_referenced = self.reversed_entry_id or self.debit_origin_id
        date_emited = fields.Datetime.context_timestamp(self, move_referenced.create_date).isoformat(
            timespec='seconds')
        doc_referenced.fechaEmisionDocFiscalReferenciado = date_emited
        doc_referenced.cufeFEReferenciada = move_referenced.cufe_electronic_invoice
        listaDocsFiscalReferenciados.append(doc_referenced)
        return listaDocsFiscalReferenciados

    def format_invoice_export_data(self):
        invoice_export = DatosFacturaExportacion()
        invoice_export.condicionesEntrega = self.invoice_incoterm_id.code
        invoice_export.monedaOperExportacion = self.currency_id.name
        if invoice_export.monedaOperExportacion != 'USD':
            exchange_value = self.env['res.currency']._get_conversion_rate(self.company_id.currency_id,
                                                                           self.currency_id,
                                                                           self.company_id,
                                                                           fields.Date.context_today(self))
            invoice_export.tipoDeCambio = float_repr(1 / exchange_value, 4)
            invoice_export.montoMonedaExtranjera = self.amount_total_signed
        return invoice_export

    def format_client_values(self):
        try:
            partner_id = self.partner_id
            assert partner_id.ei_client_type, _(
                'Field Client Type in partner is required')
            assert partner_id.ei_taxpayer_type, _(
                'Field Taxpayer Type in partner is required')
            assert partner_id.vat, _('Field NIF in partner is required')
            client = Client()
            client.tipoClienteFE = partner_id.ei_client_type
            client.tipoContribuyente = partner_id.ei_taxpayer_type
            client.numeroRUC = partner_id.vat
            client.telefono1 = None or partner_id.phone
            client.correoElectronico1 = None or partner_id.email
            client.pais = 'PA'
            client.razonSocial = partner_id.name
            client.direccion = partner_id.street
            if client.tipoClienteFE in ('01', '03'):
                assert partner_id.l10n_pa_dv, _(
                    'Field Identification code in partner is required')
                assert partner_id.business_name, _(
                    'Field Business name in partner is required')
                client.digitoVerificadorRUC = partner_id.l10n_pa_dv
                client.razonSocial = partner_id.business_name
                client.direccion = partner_id.street
                client.codigoUbicacion = partner_id.get_ebi_location_code()
                client.provincia = partner_id.ei_location_province_id.name
                client.distrito = partner_id.ei_location_district_id.name
                client.corregimiento = partner_id.ei_location_corregimiento_id.name
            if client.tipoClienteFE == '04':
                client.tipoContribuyente = None
                client.numeroRUC = ''
                client.nroIdentificacionExtranjero = partner_id.vat
                client.tipoIdentificacion = partner_id.ei_identification_type
            if self.ei_operation_destination == '1':
                client.pais = 'PA'
            else:
                client.pais = partner_id.country_id.code
            if client.tipoIdentificacion == '01':
                client.paisExtranjero = partner_id.country_id.name
            if client.pais == 'ZZ':
                # TODO: Implementar la logica del campo paisOtro
                pass
            return client
        except AssertionError as e:
            raise ValidationError(e)

    def format_transaction_data(self):
        transaction = TransactionData()
        transaction.tipoEmision = self.ei_emission_type
        transaction.tipoDocumento = self.journal_id.ei_document_type
        transaction.numeroDocumentoFiscal = self.ei_document_number
        transaction.puntoFacturacionFiscal = self.ei_document_serie
        transaction.fechaEmision = fields.Datetime.context_timestamp(self, self.create_date).isoformat(
            timespec='seconds')
        transaction.naturalezaOperacion = self.ei_nature_operation
        transaction.tipoOperacion = self.ei_operation_type
        transaction.destinoOperacion = self.ei_operation_destination
        transaction.formatoCAFE = self.ei_format_cafe
        transaction.entregaCAFE = self.ei_delivery_cafe
        transaction.envioContenedor = self.ei_container_shipping
        transaction.tipoVenta = self.ei_sale_type
        transaction.procesoGeneracion = '1'
        fieldToSearch = self.company_id.einvoice_custom_field
        if fieldToSearch:
            if fieldToSearch.endswith('id'):
                data = self[fieldToSearch].id
                transaction.informacionInteres = str(data)
            else:
                data = self[fieldToSearch]
                transaction.informacionInteres = str(data)
        return transaction

    def format_items_data(self):
        digits = 2
        items_list = []
        for i in self.invoice_line_ids.filtered(lambda x: x.price_total >= 0):
            price_ml_with_discount = i.price_unit * (1 - (i.discount / 100.0))
            item = Item()
            item.descripcion = i.name
            item.cantidad = float_repr(i.quantity, digits)
            item.precioUnitario = float_repr(i.price_unit, digits)
            item.precioUnitarioDescuento = float_repr(
                i.price_unit - (i.price_subtotal / i.quantity), digits) if i.discount else '0.00'
            item.precioItem = float_repr(i.price_subtotal, digits)
            item.valorTotal = float_repr(i.price_total, digits)
            _logger.info("SEND FE --------------------")
            _logger.info(item.cantidad)
            _logger.info(item.precioUnitario)
            _logger.info(item.precioUnitarioDescuento)
            _logger.info(item.precioItem)
            _logger.info(item.valorTotal)
            _logger.info("END FE--------------------")
            if not i.tax_ids:
                item.tasaITBMS = '00'
                item.valorITBMS = float_repr(0, digits)
            for tax in i.tax_ids:
                if 'ITBMS' in tax.name:
                    if tax.amount % 1 != 0:
                        raise ValidationError(
                            _('The "%s" tax cannot be declared with the rate of %s') % (tax.name, str(tax.amount)))
                    tasaITBMS = get_key_of_value(TASA_ITBMS, tax.amount)
                    if not tasaITBMS:
                        raise ValidationError(
                            _('Tax "%s" was not found in the catalog') % tax.name)
                    item.tasaITBMS = tasaITBMS
                    data_tax = tax.compute_all(
                        price_ml_with_discount, self.currency_id, i.quantity)
                    item.valorITBMS = float_repr(
                        data_tax['taxes'][0]['amount'], digits)
                elif 'ISC' in tax.name:
                    item.tasaISC = tax.amount
                    data_tax = tax.compute_all(
                        price_ml_with_discount, self.currency_id, i.quantity)
                    item.valorISC = float_repr(
                        data_tax['taxes'][0]['amount'], digits)
                else:
                    raise ValidationError(
                        _('It is not possible to declare the "%s" tax with electronic invoicing') % tax.name)

            items_list.append(item)
            # Si el cliente es un agente del gobierno
            if self.partner_id.ei_client_type == '03':
                item.codigoCPBS = i.cpbs_code
                item.unidadMedidaCPBS = i.cpbs_uom
        return items_list

    def format_totals_data(self, digits=2, items_data=[]):
        totals = Totals()
        totals.totalPrecioNeto = float_repr(
            sum(map(lambda x: float(x.precioItem), items_data)), digits)
        monto_itbms = 0
        monto_isc = 0
        for i in items_data:
            monto_itbms += float(i.valorITBMS) if i.valorITBMS else 0
            monto_isc += float(i.valorISC) if i.valorISC else 0
        totals.totalMontoGravado = float_repr(monto_itbms + monto_isc, digits)
        totals.totalITBMS = float_repr(0, digits)
        if monto_itbms:
            totals.totalITBMS = float_repr(monto_itbms, digits)
        if monto_isc:
            totals.totalISC = float_repr(monto_isc, digits)
        totals.totalFactura = float_repr(self.amount_total, digits)
        # TODO: Implementar el pago por cuotas
        totals.totalValorRecibido = float_repr(self.amount_total, digits)
        totals.tiempoPago = 1
        totals.nroItems = len(items_data)
        totals.totalTodosItems = float_repr(
            sum(map(lambda x: float(x.valorTotal), items_data)), digits)
        lista_desc_bonificacion, total_desc_bonificacion = self.format_desc_bonificacion()
        if len(lista_desc_bonificacion) > 0:
            totals.totalDescuento = float_repr(total_desc_bonificacion, digits)
            totals.listaDescBonificacion = lista_desc_bonificacion
        return totals

    def format_payment_data(self, digits=2):
        # TODO: Implementar el pago por cuotas
        payment = FormaPago()
        payment.formaPagoFact = '02'
        payment.valorCuotaPagada = float_repr(self.amount_total, digits)
        return payment

    def format_desc_bonificacion(self, digits=2):
        lista_desc_bonificacion = []
        total_desc_bonificacion = 0
        for item in self.invoice_line_ids.filtered(lambda x: x.price_total < 0):
            desc_bonificacion = DescuentoBonificacion()
            desc_bonificacion.descDescuento = 'Global discount'
            desc_bonificacion.montoDescuento = float_repr(
                abs(item.price_total), digits)
            total_desc_bonificacion += item.price_total
            lista_desc_bonificacion.append(desc_bonificacion)
        return lista_desc_bonificacion, abs(total_desc_bonificacion)

    def _get_key_values(self):
        codigo_sucursal_emisor = self.journal_id.ei_branch_code
        number = self.ei_document_number
        serie = self.ei_document_serie
        tipo_documento = self.journal_id.ei_document_type
        tipo_emision = self.ei_emission_type

        return (codigo_sucursal_emisor, number, serie, tipo_documento, tipo_emision)

    def action_check_status(self):
        ebi_client = self.env.company.get_ebi_client()
        params = self._get_key_values()
        res = ebi_client.consultarEstadoDocumento(*params)
        if res["codigo"] == '200':
            self.cufe_electronic_invoice = res['cufe']
            if res["estatusDocumento"] == 'Autorizada':
                self.status_fe = '03'
            elif res['estatusDocumento'] == 'Anulada':
                self.status_fe = '04'
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': res['mensajeDocumento'],
                        'type': 'success',  # types: success,warning,danger,info
                        'sticky': False,  # True/False will display for few seconds if false
                    },
                }
        else:
            raise ValidationError(res['mensaje'])

    def action_cancel_document(self, reason=None):
        if reason:
            ebi_client = self.env.company.get_ebi_client()
            params = self._get_key_values()
            res = ebi_client.anulacion(reason, *params)
            if res['codigo'] == '200':
                self.status_fe = '04'
                return {'type': 'ir.actions.act_window_close'}
            else:
                raise ValidationError(res['mensaje'])
        else:
            return {
                'name': _("Motivo"),
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'wizard.ei.cancel.reason',
                'type': 'ir.actions.act_window',
                'target': 'new'
            }

    def action_download_xml(self):
        data = self._get_key_values()
        action = {
            'type': 'ir.actions.act_url',
            'url': f'ebi_client/download_invoice?format=xml&codigo_sucursal_emisor={data[0]}&number={data[1]}&serie={data[2]}&tipo_documento={data[3]}&tipo_emision={data[4]}',
            'target': 'self'
        }
        return action

    def action_download_pdf(self):
        data = self._get_key_values()
        action = {
            'type': 'ir.actions.act_url',
            'url': f'ebi_client/download_invoice?format=pdf&codigo_sucursal_emisor={data[0]}&number={data[1]}&serie={data[2]}&tipo_documento={data[3]}&tipo_emision={data[4]}',
            'target': 'self'
        }
        return action

    def action_send_email(self):
        if not self.partner_id.email:
            raise ValidationError(_('Partner email is required'))
        params = self._get_key_values()
        ebi_client = self.env.company.get_ebi_client()
        res = ebi_client.envioCorreo(self.partner_id.email, *params)
        if res['codigo'] == '200':
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Send email'),
                    'message': res['mensaje'],
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': False,  # True/False will display for few seconds if false
                },
            }
            return notification
        raise ValidationError(res['mensaje'])


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    cpbs_code = fields.Char(string='CPBS Code')
    cpbs_uom = fields.Char(string='Unit of Mesure CPBS')

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}

        # Compute 'price_subtotal'.
        line_discount_price_unit = price_unit - \
            currency.round(price_unit * (discount / 100.0))
        subtotal = quantity * line_discount_price_unit

        # Compute 'price_total'.
        if taxes:
            taxes_res = taxes._origin.with_context(force_sign=1).compute_all(line_discount_price_unit,
                                                                             quantity=quantity, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        # In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res
