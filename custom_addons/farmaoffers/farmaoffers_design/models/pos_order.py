from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = 'pos.order'

    branch_id = fields.Many2one(
        'multi.branch',
        string="Sucursal",
        help="Sucursal asociada al pedido de Punto de Venta."
    )

    def _process_order(self, order_data, draft=False, existing_order=False):
        """
        Sobrescribe _process_order para asignar branch_id al pedido y a la factura.
        El branch_id se obtiene directamente desde pos.config.
        """
        _logger.info("Interceptando _process_order: Procesando pedido...")

        order = super(PosOrder, self)._process_order(order_data, draft, existing_order)

        if isinstance(order, int):
            order = self.browse(order)

        branch_id = order.session_id.config_id.branch_id.id if order.session_id.config_id.branch_id else False
        _logger.info(f"Branch ID obtenido desde POS Config: {branch_id}")

        if branch_id:
            order.write({'branch_id': branch_id})
            _logger.info(f"Branch ID asignado al pedido: {branch_id}")

        if order.account_move and branch_id:
            order.account_move.write({'branch_id': branch_id})
            _logger.info(f"Branch ID asignado a la factura: {order.account_move.name}")

        return order.id
