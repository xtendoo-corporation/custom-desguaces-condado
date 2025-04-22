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
    description = fields.Html(
        string="Description",
        translate=True,
        sanitize=True,
        sanitize_tags=True,
        sanitize_attributes=True
    )
    product_template_id = fields.Many2one(
        comodel_name='product.template',
        string='Product Template Reference',
        auto_join=True
    )
    product_ids = fields.One2many(
        comodel_name='product.template',
        inverse_name='product_vehicle_id',
        string='Products'
    )
    products_count = fields.Integer(
        string="Number of products",
        compute="_compute_products_count"
    )
    is_published = fields.Boolean(
        default=True
    )
    product_image_ids = fields.One2many(
        comodel_name='product.image',
        inverse_name='product_vehicle_id',
        string='Images'
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

    state = fields.Selection([
        ('published', 'Publicado'),
        ('unpublished', 'No Publicado')
    ], compute='_compute_state', store=False, string="Estado")

    @api.depends('is_published')
    def _compute_state(self):
        for record in self:
            record.state = 'published' if record.is_published else 'unpublished'

    def website_publish_button(self):
        self.ensure_one()
        self.is_published = not self.is_published
        return True

    def action_view_products(self):
        self.ensure_one()
        action = self.env.ref('product.product_template_action_all').read()[0]
        action['domain'] = [('product_vehicle_id', '=', self.id)]
        action['context'] = {'default_product_vehicle_id': self.id}
        return action
