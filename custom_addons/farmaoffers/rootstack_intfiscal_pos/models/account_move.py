from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _post(self, soft=True):
        invoice = super(AccountMove, self)._post(soft)

        if self.env.context.get('generate_electronic_invoice') and self.env.company.invoicing_mode in ('02', '03'):
            self.action_send_electronic_invoice()

        return invoice
