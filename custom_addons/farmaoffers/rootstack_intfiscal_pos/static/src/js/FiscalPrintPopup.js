odoo.define('rootstack_intfiscal_pos.FiscalPrintPopup', function (require) {
    const {useState} = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    // formerly SelectionPopupWidget
    class FiscalPrintPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({selectedId: this.props.default_printer});
        }

        selectItem(item_id) {
            this.state.selectedId = item_id;
            this.confirm();
        }

        getPayload() {
            return this.props.printers.find((item) => this.state.selectedId === item.id);
        }
    }

    FiscalPrintPopup.template = 'FiscalPrintPopup';
    FiscalPrintPopup.defaultProps = {
        printers: [],
        default_printer: false
    };

    Registries.Component.add(FiscalPrintPopup);

    return FiscalPrintPopup;
})