odoo.define('rootstack_intfiscal_pos.ClientDetailsEdit', function (require) {
    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit');
    const Registries = require('point_of_sale.Registries');

    const EbiClientDetailsEdit = ClientDetailsEdit => class extends ClientDetailsEdit {
        saveChanges() {
            this.intFields.push("ei_location_province_id", "ei_location_district_id", "ei_location_corregimiento_id")
            super.saveChanges(...arguments);
        }
    };

    Registries.Component.extend(ClientDetailsEdit, EbiClientDetailsEdit);

    return ClientDetailsEdit;
});
