from odoo import api, fields, models
from odoo.exceptions import ValidationError


class WizardEiCancelReason(models.TransientModel):
    _name = 'wizard.ei.cancel.reason'

    reason = fields.Char(string="Motivo de Anulación")

    def action_cancel_document(self):
        account_move_id = self.env['account.move'].browse(self.env.context.get('active_id'))
        res = account_move_id.action_cancel_document(self.reason)
        if res['codigo'] == '200':
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': res['mensaje'],
                    'type': 'success',
                    'sticky': False,
                },
            }
            return notification
        else:
            raise ValidationError(res['mensaje'])
