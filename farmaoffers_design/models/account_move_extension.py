from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class AccountMoveExtension(models.Model):
    _inherit = 'account.move'

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        """
        Al cambiar la sucursal, asignar el diario contable correspondiente.
        Si la sucursal no tiene un diario asociado, dejar el campo journal_id vacío.
        """
        if self.branch_id:
            _logger.info(f"Sucursal seleccionada: {self.branch_id.name}")
            if self.branch_id.journal_id:
                # Asignar el diario contable de la sucursal seleccionada
                self.journal_id = self.branch_id.journal_id
                _logger.info(f"Diario contable asignado: {self.journal_id.name}")
            else:
                # Si no hay diario asociado, dejar el campo journal_id vacío
                self.journal_id = False
                _logger.info("No se encontró un diario para la sucursal seleccionada.")
        else:
            # Si no se ha seleccionado ninguna sucursal, dejar el campo journal_id vacío
            self.journal_id = False
            _logger.info("No se seleccionó ninguna sucursal.")
