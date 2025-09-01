from odoo import models, fields

class ProductImage(models.Model):
    _name = 'product.image.custom'
    _description = 'Imágenes de productos'
    _order = 'sequence'

    name = fields.Char(
        "Nombre",
        required=True
    )
    sequence = fields.Integer(
        "Secuencia",
        default=10
    )
    image_1920 = fields.Binary(
        "Imagen",
        attachment=True
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        "Producto relacionado",
        index=True
    )
