from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_pa_delivery_zone_id = fields.Many2one(
        'l10n.pa.delivery.zone', string="Zona")
    program_name = fields.Char(string='Nombre de programa')
    affiliate_code = fields.Char(string='Código de afiliado')
