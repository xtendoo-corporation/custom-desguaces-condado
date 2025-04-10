# © 2016 Serpent Consulting Services Pvt. Ltd. (http://www.serpentcs.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Vehicle",
    "category": "e-commerce",
    "author": "Serpent Consulting Services Pvt. Ltd., "
    "Tecnativa, "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/e-commerce",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["product_brand", "website_sale", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/website_menu.xml",
        "views/product_vehicle.xml",
        #"views/product_brand_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "/website_sale_product_brand/static/src/scss/website_sale_product_brand.scss"
        ],
        "web.assets_tests": [
            "/website_sale_product_brand/static/src/js/tour.esm.js",
        ],
    },
    "installable": True,
}
