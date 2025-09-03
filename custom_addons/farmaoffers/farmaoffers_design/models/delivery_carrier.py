from odoo import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    l10n_pa_delivery_zone_ids = fields.Many2many(
        'l10n.pa.delivery.zone', 'delivery_carrier_zone_rel', 'carrier_id', 'zone_id', 'Zonas')

    def _match_address(self, partner):
        res = super(DeliveryCarrier, self)._match_address(partner)
        if self.l10n_pa_delivery_zone_ids and partner.l10n_pa_delivery_zone_id not in self.l10n_pa_delivery_zone_ids:
            return False
        return res
