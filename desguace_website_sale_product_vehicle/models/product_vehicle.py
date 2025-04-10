# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields, models, api


class ProductVehicle(models.Model):
    _name = "product.vehicle"
    _inherit = ["website.published.mixin"]
    _description = "Product Vehicle"
    _order = "name"

    name = fields.Char(
        string="Vehicle Name",
        required=True
    )
    description = fields.Text(
        translate=True
    )
    image_ids = fields.One2many(
        comodel_name='product.vehicle.image',
        inverse_name='product_vehicle_image_id',
        string='Images'
    )
    product_ids = fields.Many2many(
        comodel_name="product.template",
        inverse_name="product_vehicle_id",
        string="vehicle Products"
    )
    products_count = fields.Integer(
        string="Number of products",
        compute="_compute_products_count"
    )
    is_published = fields.Boolean(
        default=True
    )

    @api.depends("product_ids")
    def _compute_products_count(self):
        product_model = self.env["product.template"]
        groups = product_model.read_group(
            [("product_vehicle_id", "in", self.ids)],
            ["product_vehicle_id"],
            ["product_vehicle_id"],
            lazy=False,
        )
        data = {group["product_vehicle_id"][0]: group["__count"] for group in groups}
        for vehicle in self:
            vehicle.products_count = data.get(vehicle.id, 0)

