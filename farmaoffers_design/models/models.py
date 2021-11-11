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
    
    def get_general_info_by_type(self, product, filter='general'):
        items = self.env['product.general.info'].sudo().search([('product_tmpl_id', '=', product), ('type', '=', filter)])
        return items

    def get_products_with_same_compound(self, exception, filter=None):
        if filter:
            products = self.env['product.template'].sudo().search([('id', '!=', exception), ('active_compound', '=', filter)], limit=3)
            return products
        return []

    def get_product_offers(self):
        products = self.env['product.offers'].sudo().search([])
        return products
    
    def get_branch_offices(self):
        offices = self.env['branch.office'].sudo().search([])
        return offices

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

    laboratory = fields.Char(string="Laboratorio", size=60)
    presentation = fields.Char(string="Presentación", size=60)
    active_compound = fields.Char(string="Compuesto activo", size=80)
    short_description = fields.Char(string="Descripción corta", size=80)
    ribbon_ids = fields.Many2many(
        'product.ribbon', 'product_ribbon_rel', 'src_id', 'dest_id',
        string='Ribbons', help='Define your ribbons')
    aditional_info_ids = fields.One2many("product.aditional.info", "product_tmpl_id", string="Aditional information")
    general_info_ids = fields.One2many("product.general.info", "product_tmpl_id", string="General information")

    def get_all_products_with_same_compound(self, compound):
        products = self.search([('active_compound', '=', compound)])
        return products

class ResCompany(models.Model):
    _name = 'res.company'
    _inherit = "res.company"

    disclaimer = fields.Text(string="Disclaimer")

class ProductAditionalInfo(models.Model):
    _name = 'product.aditional.info'
    _description = "Aditional information for your product."

    description = fields.Text(string="Description")
    image = fields.Binary('Image', help='Image size must be 256px x 256px.')
    product_tmpl_id = fields.Many2one("product.template", string="Product")

class ProductGeneralInfo(models.Model):
    _name = 'product.general.info'
    _description = "General information for your product."

    title = fields.Char(string="title", size=60)
    description = fields.Text(string="Description")
    type = fields.Selection([('general', 'General information'), ('faq', 'Frequent questions'), ('resume', 'Product resume')], required=True, default='general')
    product_tmpl_id = fields.Many2one("product.template", string="Product")

class ProductOffers(models.Model):
    _name = 'product.offers'
    _description = "Offers."

    title = fields.Char(string="title", size=60)
    description = fields.Text(string="Description")
    image = fields.Binary('Image', help='Image size must be 256px x 256px.')

class SaleOrder(models.Model):
    _inherit = "sale.order"

    branch_office_id = fields.Many2one("branch.office", string="Branch Office")
    website_order_saving = fields.Float(
        compute='_compute_website_order_saving',
        string='Order Saving displayed on Website',
        help='Order Saving to be displayed on the website. They should not be used for computation purpose.',
    )

    @api.depends('order_line')
    def _compute_website_order_saving(self):
        for order in self:
            full_price = 0
            for line in order.order_line:
                full_price += line.price_unit * line.product_uom_qty
            order.website_order_saving = full_price - order.amount_total

class BranchOffice(models.Model):
    _name = 'branch.office'
    _description = "Branch Offices."

    name = fields.Char(string="Name", size=60)
    description = fields.Text(string="Description")
    address = fields.Text(string="Address")