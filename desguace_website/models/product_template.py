from odoo import models, fields

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    def _can_be_added_to_cart(self):
        if self.is_vehicle:
            return False
        return super(ProductTemplateInherit, self)._can_be_added_to_cart()
