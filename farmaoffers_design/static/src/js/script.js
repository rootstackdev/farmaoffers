odoo.define('farmaoffers_design.script', function (require) {
    "use strict";

    require('web.dom_ready');
    var ajax = require('web.ajax');
    var wSaleUtils = require('website_sale.utils');
    var publicWidget = require('web.public.widget');
    var sAnimations = require('website.content.snippets.animation');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');

    //theme Modify
    // New
    $(".bought-together .owl-carousel").owlCarousel({
        loop: false,
        nav: true,
        dots: false,
        autoplay: false,
        autoplayHoverPause: true,
        margin: 30,
        navText: ["<i class='fa fa-angle-double-left h3 text-primary mr-2' aria-hidden='false'></i>", "<i class='fa fa-angle-double-right h3 text-secondary' aria-hidden='false'></i>"],
        responsive: { 0: { items: 1 }, 480: { items: 2 }, 768: { items: 3 }, 991: { items: 3 }, 1200: { items: 3 } }
    });

    $(".client_reviews .owl-carousel").owlCarousel({
        loop: false,
        nav: true,
        dots: false,
        autoplay: false,
        autoplayHoverPause: true,
        margin: 30,
        navText: ["<i class='fa fa-angle-double-left h3 text-primary mr-2' aria-hidden='false'></i>", "<i class='fa fa-angle-double-right h3 text-secondary' aria-hidden='false'></i>"],
        responsive: { 0: { items: 1 }, 480: { items: 2 }, 768: { items: 3 }, 991: { items: 3 }, 1200: { items: 3 } }
    });

    $(".top_offers .owl-carousel").owlCarousel({
        loop: false,
        nav: true,
        dots: false,
        autoplay: false,
        autoplayHoverPause: true,
        margin: 0,
        navText: ["<i class='fa fa-angle-double-left h3 text-primary mr-2' aria-hidden='false'></i>", "<i class='fa fa-angle-double-right h3 text-secondary' aria-hidden='false'></i>"],
        responsive: { 0: { items: 2 }, 480: { items: 3 }, 768: { items: 5 }, 991: { items: 5 }, 1200: { items: 5 } }
    });

    $(".our_tips .owl-carousel").owlCarousel({
        loop: false,
        nav: true,
        dots: false,
        autoplay: false,
        autoplayHoverPause: true,
        autoWidth: true,
        margin: 10,
        navText: ["<i class='fa fa-angle-double-left h3 text-primary mr-2' aria-hidden='false'></i>", "<i class='fa fa-angle-double-right h3 text-secondary' aria-hidden='false'></i>"],
        responsive: { 0: { items: 2 }, 480: { items: 3 }, 768: { items: 4 }, 991: { items: 4 }, 1200: { items: 4 } }
    });

    $(".top_products .owl-carousel").owlCarousel({
        loop: false,
        nav: true,
        dots: false,
        autoplay: false,
        autoplayHoverPause: true,
        margin: 0,
        navText: ["<i class='fa fa-angle-double-left h3 text-primary mr-2' aria-hidden='false'></i>", "<i class='fa fa-angle-double-right h3 text-secondary' aria-hidden='false'></i>"],
        responsive: { 0: { items: 2 }, 480: { items: 2 }, 768: { items: 4 }, 991: { items: 5 }, 1200: { items: 5 } }
    });
    // End new

    $(".product-grid-sidebar .fo-side-list ul li a").on("click", function (e) {
        // 1
        e.preventDefault();
        // 2
        const href = $(this).attr("href");
        // 3
        $("html, body").animate({ scrollTop: $(href).offset().top }, 800);
    });


    $("#show-more-with-same-compound").on("click", function (e) {
        e.preventDefault();
        var compound = $("#current_product_compound").text().trim();
        var product_id = $(".product_template_id").val();
        var limit = undefined;
        var text = "Desplegar menos";

        if ($("#show-more-with-same-compound").text() !== "Desplegar más") {
            limit = 3;
            text = "Desplegar más";
        }

        rpc.query({

            route: "/products/same-compounds",
            params: {
                exception: product_id,
                compound: compound,
                limit: limit,
            },

        }).then(function (products) {
            $("#ul-same-compound li").remove();
            var showAll = '';
            products.forEach(element => {
                showAll += `
          <li class='font-montserrat font-size-cards'>
            <a itemprop='name' href='${element.website_url}' content='${element.name}'>${element.name}</a>
          </li>`
            })
            $("#ul-same-compound").html(showAll);
            $("#show-more-with-same-compound").html(text);
        });
    });

    toggleRadioOptions($('input:radio[name="radioSelect"]:checked'));

    /* $('input:radio[name="radioSelect"]').change(
        function () {
            toggleRadioOptions($(this));
        }
    ); */

    $('#branch_office_select').on('change', function () {
        if ($(this).val() !== "") {
            $("#branch_office_id").val($(this).val());
        }
    });

    $('#byBranchOffice').on('click', function (e) {
        e.preventDefault();

        $(".checkout_autoformat").hide();
        $("#branch_office_load").removeClass('d-none');

        $("input[name='name']").val('N/A');
        $("input[name='email']").val('noaplica@email.com');
        $("input[name='phone']").val('N/A');
        $("input[name='street']").val('N/A');
        $("input[name='city']").val('N/A');
        $("input[name='zip']").val('N/A');
        $("select[name='country_id']").val(1);
        $("input[name='is_branch_office']").val("True");
        $("form.checkout_autoformat").submit();
    });

    $(".top_products .medicine_carousel").addClass('d-block');
    $(".top_products .health_carousel").addClass('d-none');

    $('.btn_medicine').on('click', function (e) {
        e.preventDefault();
        $(".top_products .medicine_carousel").addClass('d-block');
        $(".top_products .health_carousel").addClass('d-none');
        $(".top_products .health_carousel").removeClass('d-block');

        $('.btn_medicine').removeClass('btn-gray-fo').addClass('btn-secondary');
        $('.btn_health').removeClass('btn-secondary').addClass('btn-gray-fo');
    });
    $('.btn_health').on('click', function (e) {
        e.preventDefault();
        $(".top_products .medicine_carousel").addClass('d-none');
        $(".top_products .medicine_carousel").removeClass('d-block');
        $(".top_products .health_carousel").addClass('d-block');

        $('.btn_health').removeClass('btn-gray-fo').addClass('btn-secondary');
        $('.btn_medicine').removeClass('btn-secondary').addClass('btn-gray-fo');
    });

    //Functions
    function toggleRadioOptions(data) {
        if (data.is(':checked') && data.val() === 'pickAddress') {
            // append goes here
            $("#branch_office_select").hide();
            $("#billing_fo").show();
            $("#shipping_fo").show();
            $("#is_branch_office").val("False");
        }
        if (data.is(':checked') && data.val() === 'pickBranch') {
            // append goes here
            $("#branch_office_select").show();
            $("#billing_fo").hide();
            $("#shipping_fo").hide();
            $("#is_branch_office").val("True");
        }
    }

    //Widgets
    publicWidget.registry.PaymentForm.include({
        payEvent: function (ev) {
            ev.preventDefault();
            var form = this.el;
            var checked_radio = this.$('input[type="radio"]:checked');
            var self = this;
            var is_branch_office = this.$('#is_branch_office').val();
            var branch_office_id = this.$('#branch_office_id').val();
            $('#branch_office_error').addClass("d-none")
            if (ev.type === 'submit') {
                var button = $(ev.target).find('*[type="submit"]')[0]
            } else {
                var button = ev.target;
            }

            // first we check that the user has selected a payment method
            if (checked_radio.length === 1) {
                checked_radio = checked_radio[0];

                // we retrieve all the input inside the acquirer form and 'serialize' them to an indexed array
                var acquirer_id = this.getAcquirerIdFromRadio(checked_radio);
                var acquirer_form = false;
                if (this.isNewPaymentRadio(checked_radio)) {
                    acquirer_form = this.$('#o_payment_add_token_acq_' + acquirer_id);
                } else {
                    acquirer_form = this.$('#o_payment_form_acq_' + acquirer_id);
                }
                var inputs_form = $('input', acquirer_form);
                var ds = $('input[name="data_set"]', acquirer_form)[0];

                // if the user is adding a new payment
                if (this.isNewPaymentRadio(checked_radio)) {
                    if (this.options.partnerId === undefined) {
                        console.warn('payment_form: unset partner_id when adding new token; things could go wrong');
                    }
                    var form_data = this.getFormData(inputs_form);
                    var wrong_input = false;

                    inputs_form.toArray().forEach(function (element) {
                        //skip the check of non visible inputs
                        if ($(element).attr('type') == 'hidden') {
                            return true;
                        }
                        $(element).closest('div.form-group').removeClass('o_has_error').find('.form-control, .custom-select').removeClass('is-invalid');
                        $(element).siblings(".o_invalid_field").remove();
                        //force check of forms validity (useful for Firefox that refill forms automatically on f5)
                        $(element).trigger("focusout");
                        if (element.dataset.isRequired && element.value.length === 0) {
                            $(element).closest('div.form-group').addClass('o_has_error').find('.form-control, .custom-select').addClass('is-invalid');
                            $(element).closest('div.form-group').append('<div style="color: red" class="o_invalid_field" aria-invalid="true">' + _.str.escapeHTML("The value is invalid.") + '</div>');
                            wrong_input = true;
                        }
                        else if ($(element).closest('div.form-group').hasClass('o_has_error')) {
                            wrong_input = true;
                            $(element).closest('div.form-group').append('<div style="color: red" class="o_invalid_field" aria-invalid="true">' + _.str.escapeHTML("The value is invalid.") + '</div>');
                        }
                    });

                    if (wrong_input) {
                        return;
                    }

                    this.disableButton(button);
                    // do the call to the route stored in the 'data_set' input of the acquirer form, the data must be called 'create-route'
                    return this._rpc({
                        route: ds.dataset.createRoute,
                        params: form_data,
                    }).then(function (data) {
                        // if the server has returned true
                        if (data.result) {
                            // and it need a 3DS authentication
                            if (data['3d_secure'] !== false) {
                                // then we display the 3DS page to the user
                                $("body").html(data['3d_secure']);
                            }
                            else {
                                checked_radio.value = data.id; // set the radio value to the new card id
                                form.submit();
                                return new Promise(function () { });
                            }
                        }
                        // if the server has returned false, we display an error
                        else {
                            if (data.error) {
                                self.displayError(
                                    '',
                                    data.error);
                            } else { // if the server doesn't provide an error message
                                self.displayError(
                                    _t('Server Error'),
                                    _t('e.g. Your credit card details are wrong. Please verify.'));
                            }
                        }
                        // here we remove the 'processing' icon from the 'add a new payment' button
                        self.enableButton(button);
                    }).guardedCatch(function (error) {
                        error.event.preventDefault();
                        // if the rpc fails, pretty obvious
                        self.enableButton(button);

                        self.displayError(
                            _t('Server Error'),
                            _t("We are not able to add your payment method at the moment.") +
                            self._parseError(error)
                        );
                    });
                }
                // if the user is going to pay with a form payment, then
                else if (this.isFormPaymentRadio(checked_radio)) {
                    this.disableButton(button);
                    var $tx_url = this.$el.find('input[name="prepare_tx_url"]');
                    // if there's a prepare tx url set
                    if ($tx_url.length === 1) {
                        // if the user wants to save his credit card info
                        var form_save_token = acquirer_form.find('input[name="o_payment_form_save_token"]').prop('checked');
                        // then we call the route to prepare the transaction
                        if (is_branch_office == "True" && branch_office_id == "0") {
                            $('#branch_office_error').removeClass("d-none")
                            self.enableButton(button);
                        } else {
                            return this._rpc({
                                route: $tx_url[0].value,
                                params: {
                                    'acquirer_id': parseInt(acquirer_id),
                                    'save_token': form_save_token,
                                    'access_token': self.options.accessToken,
                                    'success_url': self.options.successUrl,
                                    'error_url': self.options.errorUrl,
                                    'callback_method': self.options.callbackMethod,
                                    'order_id': self.options.orderId,
                                    'invoice_id': self.options.invoiceId,
                                    'is_branch_office': is_branch_office,
                                    'branch_office_id': branch_office_id,
                                },
                            }).then(function (result) {
                                if (result) {
                                    // if the server sent us the html form, we create a form element
                                    var newForm = document.createElement('form');
                                    newForm.setAttribute("method", self._get_redirect_form_method());
                                    newForm.setAttribute("provider", checked_radio.dataset.provider);
                                    newForm.hidden = true; // hide it
                                    newForm.innerHTML = result; // put the html sent by the server inside the form
                                    var action_url = $(newForm).find('input[name="data_set"]').data('actionUrl');
                                    newForm.setAttribute("action", action_url); // set the action url
                                    $(document.getElementsByTagName('body')[0]).append(newForm); // append the form to the body
                                    $(newForm).find('input[data-remove-me]').remove(); // remove all the input that should be removed
                                    if (action_url) {
                                        newForm.submit(); // and finally submit the form
                                        return new Promise(function () { });
                                    }
                                }
                                else {
                                    self.displayError(
                                        _t('Server Error'),
                                        _t("We are not able to redirect you to the payment form.")
                                    );
                                    self.enableButton(button);
                                }
                            }).guardedCatch(function (error) {
                                error.event.preventDefault();
                                self.displayError(
                                    _t('Server Error'),
                                    _t("We are not able to redirect you to the payment form.") + " " +
                                    self._parseError(error)
                                );
                                self.enableButton(button);
                            });
                        }
                    }
                    else {
                        // we append the form to the body and send it.
                        this.displayError(
                            _t("Cannot setup the payment"),
                            _t("We're unable to process your payment.")
                        );
                        self.enableButton(button);
                    }
                }
                else {  // if the user is using an old payment then we just submit the form
                    this.disableButton(button);
                    form.submit();
                    return new Promise(function () { });
                }
            }
            else {
                this.displayError(
                    _t('No payment method selected'),
                    _t('Please select a payment method.')
                );
                this.enableButton(button);
            }
        }
    });

    publicWidget.registry.WebsiteSale.include({
        _onChangeAttribute: function (ev) {
            if (!ev.isDefaultPrevented()) {
                ev.preventDefault();
                var show = $('.show_items_current').first().text().trim();
                var order = $('.order_items_current').first().text().trim();

                var form = $(ev.currentTarget).closest("form");

                $("<input />").attr("type", "hidden")
                    .attr("name", "show")
                    .attr("value", show)
                    .appendTo(form);
                $("<input />").attr("type", "hidden")
                    .attr("name", "order")
                    .attr("value", order)
                    .appendTo(form);


                form.submit();
            }
        },
        _changeCountry: function () {
            if (!$("#country_id").val()) {
                return;
            }
            this._rpc({
                route: "/shop/country_infos/" + $("#country_id").val(),
                params: {
                    mode: $("#country_id").attr('mode'),
                },
            }).then(function (data) {
                // placeholder phone_code
                $("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+' + data.phone_code : '');

                // populate states and display
                var selectStates = $("select[name='state_id']");
                // dont reload state at first loading (done in qweb)
                if (selectStates.data('init') === 0 || selectStates.find('option').length === 1) {
                    if (data.states.length || data.state_required) {
                        selectStates.html('');
                        _.each(data.states, function (x) {
                            var opt = $('<option>').text(x[1])
                                .attr('value', x[0])
                                .attr('data-code', x[2]);
                            selectStates.append(opt);
                        });
                        selectStates.parent('div').show();
                    } else {
                        selectStates.val('').parent('div').hide();
                    }
                    selectStates.data('init', 0);
                } else {
                    selectStates.data('init', 0);
                }

                // add zones options
                var selectZones = $("select[name='l10n_pa_delivery_zone_id']");
                if (selectZones.data('init') === 0 || selectZones.find('option').length === 1) {
                    selectZones.html('');
                    selectZones.append($('<option value="">Zonas...</option>'));
                    if (data.zones.length > 0) {
                        _.each(data.zones, function (item) {
                            var opt = $('<option>').text(item[1])
                                .attr('value', item[0]);
                            selectZones.append(opt);
                        });
                    } else {
                        selectZones.data('init', 0);
                    }
                }

                // manage fields order / visibility
                if (data.fields) {
                    if ($.inArray('zip', data.fields) > $.inArray('city', data.fields)) {
                        $(".div_zip").before($(".div_city"));
                    } else {
                        $(".div_zip").after($(".div_city"));
                    }
                    var all_fields = ["street", "zip", "city", "country_name"]; // "state_code"];
                    _.each(all_fields, function (field) {
                        $(".checkout_autoformat .div_" + field.split('_')[0]).toggle($.inArray(field, data.fields) >= 0);
                    });
                }

                if ($("label[for='zip']").length) {
                    $("label[for='zip']").toggleClass('label-optional', !data.zip_required);
                    $("label[for='zip']").get(0).toggleAttribute('required', !!data.zip_required);
                }
                if ($("label[for='zip']").length) {
                    $("label[for='state_id']").toggleClass('label-optional', !data.state_required);
                    $("label[for='state_id']").get(0).toggleAttribute('required', !!data.state_required);
                }
            });
        },
    });

    publicWidget.registry.websiteSaleDelivery.include({
        events: _.extend({}, publicWidget.registry.websiteSaleDelivery.prototype.events || {}, {
            'change #radioBranchOffice': 'onChangeShippingMode',
            'change #radioAddress': 'onChangeShippingMode',
            'change select[name="state_id"]': '_onChangeState',
        }),
        _onChangeState: function (event) {
            const state_id = event.target.value;
            if (!state_id) {
                var selectZones = $("select[name='l10n_pa_delivery_zone_id']");
                selectZones.html('');
                selectZones.append($('<option>').text('Zonas...').attr('value', ''));
                return;
            }
            this._rpc({
                route: "/shop/state_infos/" + state_id
            }).then(function (data) {
                var selectZones = $("select[name='l10n_pa_delivery_zone_id']");
                selectZones.html('');
                selectZones.append($('<option>').text('Zonas...').attr('value', ''));
                _.each(data, function (x) {
                    var opt = $('<option>').text(x.name)
                        .attr('value', x.id);
                    selectZones.append(opt);
                });
            })
        },
        _changeShippingMode: function (mode) {
            if (mode === 'branch')
                return window.location.href = '/shop/payment?is_branch_office=True';
            window.location.href = '/shop/payment';
            /* this._rpc({
                route: "/shop/update_shipping_mode",
                params: {
                    'mode': mode
                },
            }).then(function (data){
                self._handleCarrierUpdateResult.call(self,data);
                if(mode === 'branch')
                    return $('#delivery_carrier').hide();
                $('#delivery_carrier').show();
            }); */
        },
        onChangeShippingMode: function (event) {
            $('input#radioBranchOffice').prop('disabled', true);
            $('input#radioAddress').prop('disabled', true);
            $('button#o_payment_form_pay').prop('disabled', true);
            if (event.target.id === 'radioBranchOffice')
                return this._changeShippingMode('branch')
            return this._changeShippingMode('address')
        }
    });
});
