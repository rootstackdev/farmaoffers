from rootstack_ebi.catalog import TIPO_DOCUMENTO, TIPO_SUCURSAL
from odoo import api, fields, models
from odoo.addons.rootstack_intfiscal.util import convert_dict_to_list_of_tuplas


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    ei_document_type = fields.Selection(convert_dict_to_list_of_tuplas(TIPO_DOCUMENTO), string='Document Type')
    ei_branch_type = fields.Selection(convert_dict_to_list_of_tuplas(TIPO_SUCURSAL), string='Branch Type')
    ei_branch_code = fields.Char(string='Branch Code', size=4)
    sequence_id = fields.Many2one('ir.sequence', string='Sequence')
