from odoo import models, fields

class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    idLocal = fields.Char(string='ID Local')
    idEmpresa = fields.Char(string='ID Empresa')
