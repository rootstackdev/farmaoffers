odoo.define('rootstack_intfiscal.fiscal_printer', function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;

    var FiscalPrinter = AbstractAction.extend({
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.url = options.context.url;
            this.token = options.context.token;
            this.invoice_body = options.context.invoice_body;
            this.default_printer = options.context.default_printer;
        },
        loadPrinters: function () {
            let token = this.token;
            var self = this;
            $.ajax({
                url: `${this.url}/printer/printers`,
                method: 'GET',
                headers: {token},
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                timeout: 5000,
                success: function (data) {
                    self.printersArr = JSON.parse(data.printers);
                    let $printers = self.$el.find('#printers')
                    if (self.printersArr.length < 0) {
                        self.$el.append($('<div class="alert alert-danger" role="alert">\n' +
                            '  No hay impresoras configuradas!' +
                            '</div>'));
                        $printers.html('<option value="false" style="display: none"></option>');
                    } else {
                        _.each(self.printersArr, function (printer) {
                            $printers.append($('<option/>', {
                                value: printer.id,
                                text: `[${printer.port}] ${printer.model}`,
                                selected: printer.id === self.default_printer
                            }));
                            $printers.attr('disabled', false);
                            if (printer.id === self.default_printer) {
                                self.$el.find('#chk_default_printer').attr('disabled', false);
                                self.$el.find('#chk_default_printer').prop('checked', true);
                                self.$buttons.find('.js_confirm_print').attr('disabled', false);
                            }
                        });
                    }
                },
                error: function (err) {
                    self.$el.append($('<div class="alert alert-danger" role="alert">\n' +
                        '  No se pudo establecer conexión con el servidor de las impresoras!' +
                        '</div>'));
                    self.$el.find('#printers').html('<option value="false" style="display: none"></option>');
                }
            });
        },
        start: function () {
            let self = this;
            this.loadPrinters();
            this.$el.html(QWeb.render("fiscal_printer"));
            let $chk_default_printer = self.$el.find('#chk_default_printer');
            this.$el.find('#printers').on('change', function () {
                if (this.value) {
                    self.selectedPrinter = self.printersArr.filter(x => x.id === this.value)[0];
                    self.$buttons.find('.js_confirm_print').attr('disabled', false);
                    $chk_default_printer = self.$el.find('#chk_default_printer');
                    $chk_default_printer.attr('disabled', false);
                    if (self.default_printer === self.selectedPrinter.id) {
                        $chk_default_printer.prop('checked', true);
                    }
                }
            });
            $chk_default_printer.on('change', function () {
                let printer_selected_id = ''
                if (this.checked) {
                    printer_selected_id = self.$el.find('#printers').val();
                }
                self._rpc({
                    model: "ir.config_parameter",
                    method: "set_param",
                    args: ["intfiscal_default_printer", printer_selected_id],
                });
            })
        },
        printInvoice: function () {
            $.ajax({
                url: `${this.url}/printer/v2?printer_model=${this.selectedPrinter.model.toLowerCase()}&connection_port=${this.selectedPrinter.port}`,
                method: "POST",
                headers: {
                    token: this.token,
                },
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify({
                    ...this.invoice_body,
                    printerModel: this.selectedPrinter.model
                }),
                success: () => {
                    this.displayNotification({
                        title: 'Impresion fiscal',
                        message: "Factura imprimida correctamente",
                        type: 'info'
                    });
                }
            });
            self.do_action({type: 'ir.actions.act_window_close'});
        },
        renderButtons: function ($node) {
            var self = this;
            this.$buttons = $(QWeb.render("fiscal_printer_footer", {'widget': this}));
            this.$buttons.find('.js_cancel').click(function (e) {
                self.do_action({type: 'ir.actions.act_window_close'});
            });
            this.$buttons.find('.js_confirm_print').click(function (e) {
                self.printInvoice();
            })
            if ($node) {
                this.$buttons.appendTo($node);
            }
        }
    });

    core.action_registry.add('rootstack_intfiscal.fiscal_printer', FiscalPrinter);
    return {
        'FiscalPrinter': FiscalPrinter
    }
});