# © 2016 Serpent Consulting Services Pvt. Ltd. (http://www.serpentcs.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Vehicle",
    "category": "e-commerce",
    "author": "Daniel López Bermúdez, Jose Aguilar,"
    "Xtendoo",
    "website": "https://github.com/xtendoo-corporation/desguaces-condado",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "website_sale",
        "stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/website_menu.xml",
        "views/product_vehicle.xml",
        "views/product_piece.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "/desguace_website_sale_product_vehicle/static/src/scss/desguace_website_sale_product_vehicle.scss"
        ],
    },
    "installable": True,
}
