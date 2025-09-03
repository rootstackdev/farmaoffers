odoo.define("rootstack_intfiscal_pos.ReceiptScreen", function (require) {
    const Registries = require('point_of_sale.Registries');
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const session = require('web.session');

    const FiscalPrinter = (ReceiptScreen) => {
        class FiscalPrinter extends ReceiptScreen {
            async getPrinters(url, token) {
                try {
                    const data = await $.ajax({
                        url: `${url}/printer/printers`,
                        method: 'GET',
                        headers: {token},
                        dataType: "json",
                        contentType: "application/json; charset=utf-8",
                        timeout: 5000
                    });
                    return JSON.parse(data.printers);
                } catch (err) {
                    this.showPopup('ErrorPopup', {
                        title: 'Impresion Fiscal',
                        body: 'Error al comunicarse con el servidor de impresoras',
                    });
                    return false;
                }
            }

            async actionPrint(selectedPrinter, fiscalPrintData) {
                const {url, token, invoice_body} = fiscalPrintData.context;
                try {
                    await $.ajax({
                        url: `${url}/printer/v2?printer_model=${selectedPrinter.model.toLowerCase()}&connection_port=${selectedPrinter.port}`,
                        method: "POST",
                        headers: {
                            token,
                        },
                        dataType: "json",
                        contentType: "application/json; charset=utf-8",
                        data: JSON.stringify({
                            ...invoice_body,
                            printerModel: selectedPrinter.model
                        })
                    });
                } catch (e) {
                    this.showPopup('ErrorPopup', {
                        title: 'Impresion Fiscal',
                        body: 'Error al comunicarse con el servidor de impresoras',
                    });
                }
            }

            async fiscalPrint() {
                const res = await this.env.services.rpc({
                    model: 'pos.order',
                    method: 'action_print_fiscal_pos_ui',
                    args: [this.currentOrder.name]
                })
                const printers = await this.getPrinters(res.context.url, res.context.token);
                if (printers !== false) {
                    const {confirmed, payload} = await this.showPopup('FiscalPrintPopup', {
                        printers: printers === false ? [] : printers,
                        default_printer: res.context.default_printer
                    });
                    confirmed && this.actionPrint(payload, res);
                }
            }

            async downloadPdf() {
                const order_ids = this.env.pos.pos_order_ids;
                if (order_ids.length === 1 && order_ids[0].invoice_ids.length === 1) {
                    let invoice_data = order_ids[0].invoice_ids[0];
                    let action = await this.env.services.rpc({
                        model: 'account.move',
                        method: 'action_download_pdf',
                        args: [[invoice_data.id]]
                    })
                    action.url = `${session['web.base.url']}/${action.url}`;
                    this.env.pos.do_action(action)
                }
            }
        }

        return FiscalPrinter;
    };

    Registries.Component.extend(ReceiptScreen, FiscalPrinter);

    return FiscalPrinter;

})