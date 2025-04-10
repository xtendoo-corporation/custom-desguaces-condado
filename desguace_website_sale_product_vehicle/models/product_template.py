# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_vehicle_id = fields.Many2one(
        comodel_name='product.vehicle',
        string='Vehicle',
        index=True,
    )

    @api.model
    def _search_get_detail(self, website, order, options):
        res = super()._search_get_detail(website, order, options)
        domain = res["base_domain"]
        vehicle_id = options.get("vehicle")
        if vehicle_id:
            domain.append([("product_vehicle_id", "=", vehicle_id)])
        res["base_domain"] = domain
        return res
