from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _generate_pos_order_invoice(self):
        if self.session_id.config_id.invoice_journal_id.ei_document_type:
            self = self.with_context(generate_electronic_invoice=True)
        return super(PosOrder, self)._generate_pos_order_invoice()

    @api.model
    def action_print_fiscal_pos_ui(self, order_name):
        return self.search([('pos_reference', '=', order_name)]).account_move.intfiscal_print()

    @api.model
    def create_from_ui(self, orders, draft=False):
        data = super(PosOrder, self).create_from_ui(orders, draft)
        for item in data:
            item['invoice_ids'] = self.env['account.move'].search_read(domain=[('pos_order_ids', 'in', [item['id']])],
                                                                       fields=['id', 'name'])
        return data
