# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


# class farmaoffers_design(models.Model):
#     _name = 'farmaoffers_design.farmaoffers_design'
#     _description = 'farmaoffers_design.farmaoffers_design'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

class website(models.Model):
    _inherit = 'website'

    def get_price_filter(self):
        price_filter_fo = self.env['price.filter'].sudo().search([], limit=1, order='sequence')
        return price_filter_fo
    
    def get_product_attributes(self):
        attributes = self.env['product.attribute'].sudo().search([])
        return attributes

class PriceFilter(models.Model):
    _name = 'price.filter'
    _description = "shows the values for price filter on product list page."
    _order = 'sequence'

    price_under = fields.Float('Precio desde', digits=(12,6), default=100)
    price_over = fields.Float('Precio hasta', digits=(12,6), default=1000)
    price_range = fields.Float('Rango de precios', digits=(12,6), default=1000)
    sequence = fields.Integer('Sequence', default=10)

    @api.constrains('price_over')
    def _over_is_greater_than_under(self):
        for record in self:
            if record.price_over < record.price_under :
                raise ValidationError("Your record must be greater than: %s" % record.price_under)

    def __str__(self):
        return "Price filter: under is %s, over is %s, range is %s" % (self.price_under, self.price_over, self.price_range)

class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = "product.template"

    ribbon_ids = fields.Many2many(
        'product.ribbon', 'product_ribbon_rel', 'src_id', 'dest_id',
        string='Ribbons', help='Define your ribbons')