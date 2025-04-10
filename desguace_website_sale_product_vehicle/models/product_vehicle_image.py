from odoo import fields, models, api


class ProductVehicleImage(models.Model):
    _name = 'product.vehicle.image'
    _description = 'Vehicle Image'
    _order = 'sequence'

    name = fields.Char(string="Name")

    # The sequence of the image in the list.
    sequence = fields.Integer(default=10)

    # The image itself, stored as a binary field.
    image = fields.Binary(
        string="Image",
        required=True,
        attachment=True
    )

    # The image name, used for display purposes.
    product_vehicle_image_id = fields.Many2one(
        comodel_name='product.vehicle',
        string='Vehicle',
        required=True,
        ondelete='cascade'
    )
