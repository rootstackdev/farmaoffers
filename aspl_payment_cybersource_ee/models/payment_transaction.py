# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

import logging
from odoo import _, api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TxCybersource(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on transfer data.

        :param str provider: The provider of the provider that handled the transaction
        :param dict data: The transfer feedback data
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'cybersource':
            return tx

        reference = notification_data.get('reference')
        if not reference:
            reference = notification_data.get('processingValues', {}).get('reference')
        tx = self.search(
            [('reference', '=', reference), ('provider_code', '=', 'cybersource')],
            limit=1,
        )
        if not tx:
            raise ValidationError(
                _("No se encontró una transacción de CyberSource con referencia %s.", reference)
            )
        return tx

    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on data.

        Note: self.ensure_one()

        :param dict data: The feedback data
        :return: None
        :raise: ValidationError if inconsistent data were received
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != "cybersource":
            return

        reason_code = notification_data.get('reason_code')
        request_id = notification_data.get('request_id')
        state_message = notification_data.get('reason')
        if request_id:
            self.provider_reference = request_id

        if reason_code == 100:
            self._set_done(state_message=state_message)
        elif reason_code == 480:
            self._set_pending(state_message=state_message)
        else:
            self._set_error(state_message or _("CyberSource rechazó la transacción."))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
