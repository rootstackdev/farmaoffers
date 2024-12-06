from odoo import models, fields

class PosOrder(models.Model):
    _inherit = 'pos.order'

    branch_id = fields.Many2one(
        comodel_name='multi.branch',
        string="Sucursal",
        compute='_compute_branch_id',
        store=True,
        help="Sucursal asociada al Punto de Venta.",
    )

    @api.depends('session_id.config_id.branch_id')
    def _compute_branch_id(self):
        for order in self:
            order.branch_id = order.session_id.config_id.branch_id