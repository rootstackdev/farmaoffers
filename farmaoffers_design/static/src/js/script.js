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
  
  $(".product-grid-sidebar .fo-side-list ul li a").on("click", function (e) {
    // 1
    e.preventDefault();
    // 2
    const href = $(this).attr("href");
    // 3
    $("html, body").animate({ scrollTop: $(href).offset().top }, 800);
  });


  $("#show-more-with-same-compound").on("click", function(e) {
    e.preventDefault();
    var compound = $("#current_product_compound").text();
    var limit = undefined;
    var text = "Desplegar menos"
    if($("#show-more-with-same-compound").text() !== "Desplegar más") {
      limit = 3
      text = "Desplegar más"
    }

    rpc.query({

      route: "/products/same-compounds",
      params: {
        compound: compound,
        limit: limit,
      },

    }).then(function (products) {
        $( "#ul-same-compound li" ).remove();
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
});
