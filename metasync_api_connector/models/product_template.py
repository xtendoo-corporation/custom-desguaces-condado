from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # id_company = fields.Integer(
    #     string='ID Empresa',
    # )
    principal_ref = fields.Char(
        string='Referencia Principal',
    )
    vehicle_id = fields.Char(
        string='ID Vehículo',
    )
    version_code = fields.Char(
        string='Código Versión',
    )
    article_code = fields.Char(
        string='Código Artículo',
    )
    stock_year = fields.Char(
        string='Año Stock',
    )
    location = fields.Char(
        string='Ubicación',
    )
    observations = fields.Text(
        string='Observaciones',
    )
    reserve = fields.Integer(
        string='Reserva',
    )
    material_type = fields.Char(
        string='Tipo Material',
    )
    modification_date = fields.Datetime(
        string='Fecha Modificación',
    )
    cod_almacen = fields.Integer(
        string='Código Almacén',
    )

