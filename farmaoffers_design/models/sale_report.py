from odoo import models, fields


class SaleReport(models.Model):
    _inherit = 'sale.report'

    standard_price = fields.Float(string='Costo Producto', readonly=True)

    def _select_additional_fields(self, fields):
        fields['standard_price'] = ", prop.value_float AS standard_price"
        return super()._select_additional_fields(fields)

    def _from_sale(self, from_clause=''):
        res = super()._from_sale(from_clause)
        res += """
            JOIN ir_property prop on prop.res_id = 'product.product,' || p.id"""
        return res

    def _group_by_sale(self, groupby=''):
        res = super()._group_by_sale(groupby)
        res += """
            ,prop.value_float"""
        return res
