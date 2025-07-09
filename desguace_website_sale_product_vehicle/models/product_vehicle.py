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
    website_ribbon_id = fields.Many2one(
        string="Ribbon",
        comodel_name='product.ribbon'
    )

    # Campos específicos del vehículo según Metasync
    id_local = fields.Integer(string='ID Local')
    id_empresa = fields.Integer(string='ID Empresa')
    codigo = fields.Char(string='Código')
    bastidor = fields.Char(string='Bastidor')
    matricula = fields.Char(string='Matrícula')
    color = fields.Char(string='Color')
    kilometraje = fields.Integer(string='Kilometraje')
    anyo_vehiculo = fields.Integer(string='Año del vehículo')
    codigo_motor = fields.Char(string='Código Motor')
    codigo_cambio = fields.Char(string='Código Cambio')
    observaciones = fields.Text(string='Observaciones')

    # Datos técnicos
    marca = fields.Char(string='Marca')
    modelo = fields.Char(string='Modelo')
    version = fields.Char(string='Versión')
    combustible = fields.Char(string='Combustible')
    puertas = fields.Integer(string='Puertas')
    potencia_hp = fields.Integer(string='Potencia HP')
    potencia_kw = fields.Integer(string='Potencia KW')
    cilindrada = fields.Integer(string='Cilindrada')
    transmision = fields.Char(string='Transmisión')
    num_marchas = fields.Integer(string='Número de marchas')

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
        ('published', 'Published'),
        ('unpublished', 'Unpublished')
    ], compute='_compute_state', store=False, string="State")

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

    def sync_vehicle_data(self):
        """Sincroniza los datos del vehículo con Metasync"""
        RecoverWizard = self.env['recover.changes.stock.company.metasync.wizard']

        # Obtener parámetros de configuración
        api_key = self.env['ir.config_parameter'].sudo().get_param('metasync.inventory.apikey')
        id_empresa = self.env['ir.config_parameter'].sudo().get_param('metasync.id_empresa')

        if not api_key or not id_empresa:
            raise UserError('Falta configurar los parámetros de Metasync')

        # Crear instancia temporal del wizard
        wizard = RecoverWizard.create({
            'fecha': datetime.now(),
            'lastid': '0',
            'offset': 1000
        })

        try:
            # Ejecutar la sincronización usando el método existente
            result = wizard.recuperar_cambios_almacen_empresa_metasync()

            # Procesar solo los vehículos que coincidan con el ID local
            if result and 'vehiculos' in result:
                for vehiculo in result['vehiculos']:
                    if vehiculo['idLocal'] == self.id_local:
                        # Actualizar campos del vehículo
                        self.write({
                            'name': f"{vehiculo['nombreMarca']} {vehiculo['nombreModelo']}",
                            'matricula': vehiculo['matricula'],
                            'bastidor': vehiculo['bastidor'],
                            'color': vehiculo['color'],
                            'kilometraje': vehiculo['kilometraje'],
                            'anyo_vehiculo': vehiculo['anyoVehiculo'],
                            'codigo_motor': vehiculo['codigoMotor'],
                            'codigo_cambio': vehiculo['codigoCambio'],
                            'observaciones': vehiculo['observaciones'],
                            'combustible': vehiculo['combustible'],
                            'puertas': vehiculo['puertas'],
                            'potencia_hp': vehiculo['potenciaHP'],
                            'potencia_kw': vehiculo['potenciaKw'],
                            'cilindrada': vehiculo['cilindrada'],
                            'transmision': vehiculo['transmision'],
                            'num_marchas': vehiculo['numMarchas']
                        })
                        break

            return {'type': 'ir.actions.client', 'tag': 'reload'}

        except Exception as e:
            raise UserError(f'Error al sincronizar: {str(e)}')
        finally:
            # Limpiar el wizard temporal
            wizard.unlink()
