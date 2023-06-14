from odoo.addons.portal.controllers.portal import CustomerPortal


class FarmaofferCustomerPortal(CustomerPortal):
    OPTIONAL_BILLING_FIELDS = CustomerPortal.OPTIONAL_BILLING_FIELDS + ['program_name', 'affiliate_code']
