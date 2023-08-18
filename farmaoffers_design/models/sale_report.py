import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class SaleReport(models.Model):
    _inherit = "sale.report"

    standard_price = fields.Float(string="Costo Producto", readonly=True)

    def _select_additional_fields(self, fields):
        return super()._select_additional_fields(fields)

    def _select_sale(self, fields=None):
        res = super()._select_sale(fields)
        res += ",prop.value_float AS standard_price"
        return res

    def _from_sale(self, from_clause=""):
        res = super()._from_sale(from_clause)
        res += """
            JOIN ir_property prop on prop.res_id = 'product.product,' || p.id"""
        return res

    def _group_by_sale(self, groupby=""):
        res = super()._group_by_sale(groupby)
        res += """
            ,prop.value_float"""
        return res

    def _select_pos(self, fields=None):
        res = super()._select_pos(fields)
        res += ",prop.value_float AS standard_price"
        return res

    def _from_pos(self):
        res = super()._from_pos()
        res += """
            JOIN ir_property prop on prop.res_id = 'product.product,' || p.id"""
        return res

    def _group_by_pos(self):
        res = super()._group_by_pos()
        res += """,prop.value_float"""
        return res
