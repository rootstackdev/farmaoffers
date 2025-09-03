from odoo import api, fields, models


class EbiLocationMixin(models.AbstractModel):
    _name = 'ebi.location.mixin'
    _description = 'Mixin model to store the codes of locations'

    code = fields.Char(string='Code', size=1)
    name = fields.Char(string='Name')


class EbiLocationProvince(models.Model):
    _name = 'ebi.location.province'
    _inherit = 'ebi.location.mixin'


class EbiLocationDistrict(models.Model):
    _name = 'ebi.location.district'
    _inherit = 'ebi.location.mixin'


class EbiLocationCorregimiento(models.Model):
    _name = 'ebi.location.corregimiento'
    _inherit = 'ebi.location.mixin'
