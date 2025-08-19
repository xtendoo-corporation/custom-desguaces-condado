from odoo import fields, models, api

class ProductVehicleImage(models.Model):
    _name = "product.vehicle.image"
    _description = "Vehicle Image"
    _order = "sequence, id"

    vehicle_id = fields.Many2one(
        'product.vehicle',
        string='Vehículo',
        ondelete='cascade',
        required=True
    )
    url = fields.Char("URL Imagen", required=True)
    sequence = fields.Integer("Orden", default=10)
