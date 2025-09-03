odoo.define('rootstack_intfiscal.message', function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');

    var FiscalMessage = AbstractAction.extend({
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.message = options.context.message;
        },
        start: function () {
            this.$el.html(this.message);
        },
        renderButtons: function ($node) {
            var self = this;
            this.$buttons = $('<button class="btn btn-secondary js_cancel">Cerrar</button>');
            this.$buttons.click(function (e) {
                self.do_action({type: 'ir.actions.act_window_close'});
            });
            if ($node) {
                this.$buttons.appendTo($node);
            }
        }
    });

    core.action_registry.add('rootstack_intfiscal.message', FiscalMessage);
    return {
        'FiscalMessage': FiscalMessage
    }
});