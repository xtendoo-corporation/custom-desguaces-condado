from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'

    default_code = fields.Char(string='Código', required=True)
