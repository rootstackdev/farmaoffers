from odoo import models, fields


class DeliveryZone(models.Model):
    _description = "Delivery Zone"
    _name = "l10n.pa.delivery.zone"

    name = fields.Char(string="Nombre")
    code = fields.Char(string="Codigo")
    state_id = fields.Many2one(
        "res.country.state", string="Estado / Provincia")


class CountryState(models.Model):
    _inherit = 'res.country.state'

    zone_ids = fields.One2many(
        "l10n.pa.delivery.zone", "state_id", string="Zonas")
