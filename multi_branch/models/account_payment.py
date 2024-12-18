# See LICENSE file for full copyright and licensing details.
"""Account and Payment Related Models."""

from odoo import api, fields, models


class AccountPayment(models.Model):
    """Account Payment."""

    _inherit = "account.payment"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")

    @api.model
    def default_get(self, fields):
        """Overridden Method to update branch in Payment."""
        rec = super(AccountPayment, self).default_get(fields)
        active_ids = self._context.get("active_ids") or self._context.get("active_id")
        invoices = (
            self.env["account.move"]
            .browse(active_ids)
            .filtered(lambda move: move.is_invoice(include_receipts=True))
        )
        if invoices:
            rec["branch_id"] = (
                invoices[0].branch_id and invoices[0].branch_id.id or False
            )
        return rec

    def post(self):
        """Overridden Method to update branch in payment."""
        res = super(AccountPayment, self).post()
        for payment in self:
            if payment.invoice_ids and not payment.branch_id:
                for invoice in payment.invoice_ids:
                    payment.branch_id = (
                        invoice.branch_id and invoice.branch_id.id or False
                    )
                    break
        return res

    def _prepare_payment_moves(self):
        """Overridden Method to update branch in payment move lines."""
        self.ensure_one()
        all_move_vals = super(AccountPayment, self)._prepare_payment_moves()
        for move_val in all_move_vals:
            move_val.update(
                {"branch_id": self.branch_id and self.branch_id.id or False}
            )
            for line_val in move_val.get("line_ids", []):
                if line_val and len(line_val) >= 3:
                    line_val[2].update(
                        {"branch_id": self.branch_id and self.branch_id.id or False}
                    )
        return all_move_vals


class AccountMoveLine(models.Model):
    """Account Move Line."""

    _inherit = "account.move.line"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")


class AccountMove(models.Model):
    """Account Move."""

    _inherit = "account.move"

    branch_id = fields.Many2one(
        "multi.branch",
        string="Branch Name",
        default=lambda self: self.env.user.branch_id,
        ondelete="restrict",
    )

    @api.model
    def create(self, vals):
        """Overridden create method to update the lines."""
        new_move = super(AccountMove, self).create(vals)
        if new_move and new_move.branch_id:
            if new_move.line_ids:
                new_move.line_ids.write(
                    {"branch_id": new_move.branch_id and new_move.branch_id.id or False}
                )
            if new_move.invoice_line_ids:
                new_move.invoice_line_ids.write(
                    {"branch_id": new_move.branch_id and new_move.branch_id.id or False}
                )
        return new_move

    def write(self, vals):
        """Overridden write method to update the lines."""
        res = super(AccountMove, self).write(vals)
        if vals.get("branch_id", False):
            for inv in self:
                if inv and inv.branch_id:
                    if inv.line_ids:
                        inv.line_ids.write(
                            {"branch_id": inv.branch_id and inv.branch_id.id or False}
                        )
                    if inv.invoice_line_ids:
                        inv.invoice_line_ids.write(
                            {"branch_id": inv.branch_id and inv.branch_id.id or False}
                        )
        return res
