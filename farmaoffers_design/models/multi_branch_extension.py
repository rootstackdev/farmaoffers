from odoo import models, fields

class MultiBranchExtension(models.Model):
    _inherit = 'multi.branch'

    ei_branch_type = fields.Char(
        string='Tipo de Sucursal',
        required=True,  
        help='Tipo de Sucursal utilizado para la facturación electrónica.'
    )
    ei_branch_code = fields.Char(
        string='Código de Sucursal Emisor',
        required=True,  
        help='Código de la sucursal emisora utilizado para la facturación electrónica.'
    )
