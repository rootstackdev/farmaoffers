# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

class Website(models.Model):

    _inherit = "website"
    whatsapp_number = fields.Char('Numero de whatsapp')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    whatsapp_number = fields.Char(related='website_id.whatsapp_number', readonly=False)

    @api.depends('website_id', 'whatsapp_number')
    def has_whatsapp(self):
        self.has_whatsapp = self.whatsapp_number

    def inverse_has_whatsapp(self):
        if not self.has_whatsapp:
            self.whatsapp_number = ''

    has_whatsapp = fields.Boolean(
        "Configurar Whatsapp", compute=has_whatsapp, inverse=inverse_has_whatsapp
    )
