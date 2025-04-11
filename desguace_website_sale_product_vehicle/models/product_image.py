from odoo import api, models, fields

class ProductImage(models.Model):
    _name = "product.image"
    _inherit = "product.image"

    product_vehicle_id = fields.Many2one(
        comodel_name='product.vehicle',
        string='Vehicle',
        index=True
    )
