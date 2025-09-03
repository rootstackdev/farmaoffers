from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.rootstack_intfiscal.util import convert_dict_to_list_of_tuplas

class ResCompany(models.Model):
    _inherit = 'res.company'

    ruc = fields.Many2one("ir.model.fields", string="ruc", domain="[('model_id.model','=','res.partner')]")
    dv = fields.Many2one("ir.model.fields", string="dv", domain="[('model_id.model','=','res.partner')]")
    tipo_contribuyente = fields.Many2one("ir.model.fields", string="tipo_contribuyente",
                                         domain="[('model_id.model','=','res.partner')]")
    invoicing_mode = fields.Selection([
        ('01', 'Fiscal Printing'),
        ('02', 'Electronic Invoice'),
        ('03', 'Fiscal Printing + Electronic Invoice')
    ], string='Invoicing Mode')
    einvoice_ws_host = fields.Char(string='Server WSDL')
    einvoice_ws_token = fields.Char(string='Token')
    einvoice_ws_password = fields.Char(string='Password')
    einvoice_custom_field = fields.Selection(selection='_get_field_account_move', string='Campo personalizado', translate=True)


    def get_ebi_client(self):
        try:
            assert self.einvoice_ws_host, _('Field Server WSDL on company settings is required')
            assert self.einvoice_ws_token, _('Field Token on company settings is required')
            assert self.einvoice_ws_password, _('Field Password on company settings is required')
            from rootstack_ebi.ebi_client import EbiClient
            return EbiClient(self.einvoice_ws_host, self.einvoice_ws_token, self.einvoice_ws_password)
        except AssertionError as error:
            raise ValidationError(error)
        
    def _get_field_account_move(self):
        model_fields = self.env['account.move']._fields
        my_fields = convert_dict_to_list_of_tuplas(model_fields)
        field_selection = []
        for key in my_fields:
            field_selection.append((key[0], key[0]))
        return field_selection
            
                


    
