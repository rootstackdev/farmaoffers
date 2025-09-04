{
    "name": "Theme Grocery",
    "version": "18.0.0.1",
    "summary": "Ecommerce theme for grocery/food stores.",
    "description": "Online Supermarket theme.",
    "license": "OPL-1",
    "author": "Kanak Infosystems LLP.",
    "category": "Theme/Website",
    "depends": [
        "website",
        "website_sale",
        "website_sale_wishlist",
        "website_sale_comparison",
        "website_mass_mailing",
        "mass_mailing",
        "website_blog"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/views.xml",
        "views/customize_show_templates.xml",
        "views/h_f_templates.xml",
        "views/homepage_templates.xml",
        "views/shop_templates.xml",
        "views/product_details_templates.xml",
        "views/snippets.xml",
    ],
    "assets": {
        # Variables primarias (bootstrap + design tokens): aquí van overrides de variables
        "web._assets_primary_variables": [
            "theme_grocery/static/src/scss/customise_variables.scss"
        ],
        "website.assets_frontend": [
            "theme_grocery/static/src/scss/style.scss",
            "theme_grocery/static/description/favicon.ico",
            "theme_grocery/static/lib/ion.rangeSlider-2.3.1/css/ion.rangeSlider.css",
            "theme_grocery/static/lib/OwlCarousel/owl.carousel.min.css",
            "theme_grocery/static/lib/malihu-custom-scrollbar/jquery.mCustomScrollbar.min.css",
            "theme_grocery/static/src/css/style.css",
            "theme_grocery/static/src/js/quick_view_dialog.js",
            "theme_grocery/static/src/js/price_filter.js",
            "theme_grocery/static/lib/ion.rangeSlider-2.3.1/js/ion.rangeSlider.js",
            "theme_grocery/static/lib/OwlCarousel/owl.carousel.min.js",
            "theme_grocery/static/lib/malihu-custom-scrollbar/jquery.mCustomScrollbar.concat.min.js",
            "theme_grocery/static/src/js/script.js"
        ]
    },
    "demo": ["demo/theme_grocery_demo.xml"],
    "installable": True,
    "application": True,
    "images": [
        "static/description/theme_grocery.jpg",
        "static/description/theme_grocery_screenshot.jpg",
    ],
}
