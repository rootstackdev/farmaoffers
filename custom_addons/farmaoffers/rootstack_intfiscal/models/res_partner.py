from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.rootstack_intfiscal.util import convert_dict_to_list_of_tuplas
from rootstack_ebi.catalog import TIPO_CLIENTE_FE, TIPO_CONTRIBUYENTE, TIPO_IDENTIFICACION


class ResPartner(models.Model):
    _inherit = 'res.partner'

    business_name = fields.Char(string='Business Name')
    l10n_pa_dv = fields.Char("Identification code")
    ei_client_type = fields.Selection(convert_dict_to_list_of_tuplas(TIPO_CLIENTE_FE), string='Client Type')
    ei_taxpayer_type = fields.Selection(convert_dict_to_list_of_tuplas(TIPO_CONTRIBUYENTE), string='Taxpayer Type')
    ei_identification_type = fields.Selection(convert_dict_to_list_of_tuplas(TIPO_IDENTIFICACION),
                                              string='Identification Type')
    ei_location_province_id = fields.Many2one('ebi.location.province', string='Province')
    ei_location_district_id = fields.Many2one('ebi.location.district', string='District')
    ei_location_corregimiento_id = fields.Many2one('ebi.location.corregimiento', string='Corregimiento')

    def check_electronic_invoice_fields(self):
        try:
            assert self.ei_client_type, 'Field client type in required'
            assert self.ei_taxpayer_type, 'Field taxpayer type in required'
            if self.ei_client_type in ('01', '03'):
                assert self.l10n_pa_dv, 'Field identification code (DV) is required'
        except AssertionError as error:
            raise ValidationError(error)

    def action_check_document_ruc(self):
        try:
            assert self.ei_taxpayer_type, _('Field taxpayer type in required')
            ebi_client = self.env.company.get_ebi_client()
            res = ebi_client.consultarRucDV(self.ei_taxpayer_type, self.vat)
            if res['codigo'] == '200':
                self.l10n_pa_dv = res['infoRuc']['dv']
                self.business_name = res['infoRuc']['razonSocial']
            else:
                raise ValidationError(res['mensaje'])
        except Exception as error:
            raise ValidationError(error)

    def get_ebi_location_code(self):
        if self.ei_location_province_id and self.ei_location_district_id and self.ei_location_corregimiento_id:
            return f'{self.ei_location_province_id.code}-{self.ei_location_district_id.code}-{self.ei_location_corregimiento_id.code}'
        return None
