from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request, route


class FarmaofferCustomerPortal(CustomerPortal):
    OPTIONAL_BILLING_FIELDS = CustomerPortal.OPTIONAL_BILLING_FIELDS + ['patient_program_ids',]

    def details_form_validate(self, data):
        patient_program_values = []
        patient_program_ids = set()
        new_patient_program_ids = set()
        temp = {}
        fields = list(data.keys())
        for field in fields:
            if field.startswith('program_name') or field.startswith('affiliate_code'):
                if field.endswith('new'):
                    new_patient_program_ids.add(int(field.split('_')[2]))
                else:
                    patient_program_ids.add(int(field.split('_')[2]))
                temp[field] = data.pop(field)
        
        for patient_id in patient_program_ids:
            name = temp['program_name_' + str(patient_id)] 
            code = temp['affiliate_code_' + str(patient_id)]
            if (not name and not code) or (not name and code):
                continue 
            patient_program_values.append(
                (
                    1, patient_id, {
                        'program_name': name,
                        'affiliate_code': code,
                    }
                )
            )
        
        for patient_id in new_patient_program_ids:
            name = temp['program_name_' + str(patient_id) + '_new'] 
            code = temp['affiliate_code_' + str(patient_id) + '_new']
            if (not name and not code) or (not name and code):
                continue 
            patient_program_values.append(
                (
                    0, 0, {
                        'program_name': name,
                        'affiliate_code': code,
                    }
                )
            )
        
        res = super().details_form_validate(data)
        data.update({'patient_program_ids': patient_program_values, **temp})
        return res
