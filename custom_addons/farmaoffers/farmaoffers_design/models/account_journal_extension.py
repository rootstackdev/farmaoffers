from odoo import models, fields
from rootstack_ebi.catalog import TIPO_DOCUMENTO, TIPO_SUCURSAL
from odoo.addons.rootstack_intfiscal.util import convert_dict_to_list_of_tuplas

class AccountJournalExtension(models.Model):
    _inherit = 'account.journal'

    ei_branch_type = fields.Char(
        related='branch_id.ei_branch_type',  
        string='Branch Type',
        required=True,
        help='Tipo de Sucursal utilizado para la facturación electrónica.'
    )
    ei_branch_code = fields.Char(
        related='branch_id.ei_branch_code', 
        string='Branch Code',
        required=True,
        help='Código de la sucursal emisora utilizado para la facturación electrónica.'
    )

    ei_document_type = fields.Selection(convert_dict_to_list_of_tuplas(TIPO_DOCUMENTO), string='Document Type')
    sequence_id = fields.Many2one('ir.sequence', string='Sequence')
