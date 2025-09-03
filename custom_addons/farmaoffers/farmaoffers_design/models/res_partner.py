from odoo import models, fields


class PartnerPatientProgram(models.Model):
    _name = 'res.partner.patient.program'
    _description = 'Programa de pacientes'

    partner_id = fields.Many2one('res.partner', string='Contacto')
    program_name = fields.Char(string='Nombre de programa')
    affiliate_code = fields.Char(string='Código de afiliado')

class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_pa_delivery_zone_id = fields.Many2one(
        'l10n.pa.delivery.zone', string="Zona")
    patient_program_ids = fields.One2many('res.partner.patient.program', 'partner_id', string='Programas de paciente')
