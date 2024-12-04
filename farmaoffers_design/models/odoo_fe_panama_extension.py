import threading
import logging
from odoo import models, _
from rootstack_ebi.document import ElectronicDocument

_logger = logging.getLogger(__name__)


lock_send_einvoice = threading.Lock()

class AccountMoveFEExtension(models.Model):
    _inherit = 'account.move'

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
            totals.listaFormaPago = [payment]
            edocument.totalesSubTotales = totals
            edocument.tipoSucursal = self.branch_id.ei_branch_type 
            edocument.codigoSucursalEmisor = self.branch_id.ei_branch_code

        try:
            # Crea un diccionario manualmente para visualizar los datos
            edocument_dict = {
                "cliente": repr(edocument.datosTransaccion.cliente),
                "datosTransaccion": repr(edocument.datosTransaccion),
                "listaItems": [repr(item) for item in edocument.listaItems],
                "totalesSubTotales": repr(edocument.totalesSubTotales),
                "listaFormaPago": [repr(forma_pago) for forma_pago in edocument.totalesSubTotales.listaFormaPago],
                "tipoSucursal": edocument.tipoSucursal,
                "codigoSucursalEmisor": edocument.codigoSucursalEmisor,
            }

            _logger.info("Datos del documento electrónico a enviar: %s", edocument_dict)
        except Exception as e:
            _logger.error("Error al procesar los datos del documento: %s", e)

        response = self.send_edocument_to_webservice(edocument)
        sequence_id._next_do()
        self.env.cr.commit()
        return response
