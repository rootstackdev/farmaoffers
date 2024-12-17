odoo.define('farmaoffers_design.OrderReceipt', function (require) {
    "use strict";

    const models = require('point_of_sale.models');
    const PosModel = models.PosModel;

    // Extender el modelo pos.config para incluir datos de la sucursal
    models.load_models([
        {
            model: 'multi.branch', // El modelo de sucursales
            fields: ['id', 'name', 'street', 'street2', 'state_id', 'city'],
            domain: function (self) {
                return [['id', '=', self.config.branch_id[0]]]; // Filtrar por la sucursal vinculada al POS
            },
            loaded: function (self, branches) {
                if (branches.length) {
                    self.branch_info = branches[0]; // Almacenar los datos completos de la sucursal
                } else {
                    self.branch_info = {
                        id: null,
                        name: "",
                        street: "",
                        street2: "",
                        state_id: "",
                        city: ""
                    };
                }

                console.log("Datos completos de la sucursal cargados:", self.branch_info);
            },
        },
    ]);

    // Extender la inicialización del PosModel para verificar la información de la sucursal
    const _super_PosModelLoaded = PosModel.prototype.initialize;
    PosModel.prototype.initialize = function (session, attributes) {
        const self = this;

        // Llamar al método original
        _super_PosModelLoaded.call(this, session, attributes);

        // Verificar que los datos se cargaron
        this.ready.then(() => {
            console.log("Datos de la sucursal disponibles en POS:", this.branch_info);
        });
    };
});
