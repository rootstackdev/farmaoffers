from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    intfiscal_url = fields.Char()
    intfiscal_token = fields.Char()
    intfiscal_default_printer = fields.Char()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['intfiscal_url'] = self.env['ir.config_parameter'].sudo().get_param('intfiscal_url', default="")
        res['intfiscal_token'] = self.env['ir.config_parameter'].sudo().get_param('intfiscal_token', default="")
        res['intfiscal_default_printer'] = self.env['ir.config_parameter'].sudo().get_param('intfiscal_default_printer',
                                                                                            default="")
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('intfiscal_url', self.intfiscal_url)
        self.env['ir.config_parameter'].sudo().set_param('intfiscal_token', self.intfiscal_token)
        self.env['ir.config_parameter'].sudo().set_param('intfiscal_default_printer', self.intfiscal_default_printer)
        super(ResConfigSettings, self).set_values()
