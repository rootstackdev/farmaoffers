from odoo import api, models

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):

        """
        Compute the amounts of the SO line.
        """
        for line in self:
            currency = line.currency_id or line.company_id.currency_id
            price = line.price_unit - currency.round( line.price_unit * ((line.discount or 0.0) / 100.0))
            taxes = line.tax_id.compute_all(
                price, 
                line.order_id.currency_id, 
                line.product_uom_qty, 
                product=line.product_id, 
                partner=line.order_id.partner_shipping_id
            )
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
