# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields, models, api


class ProductVehicle(models.Model):
    _name = "product.vehicle"
    _inherit = ["website.published.mixin"]
    _description = "Product Vehicle"
    _order = "name"

    # Campos existentes necesarios para integraciones
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

    # Campos de identificación Metasync
    id_local = fields.Char(
        string='ID Local',
        index=True,
        help="Local ID for the vehicle, used for synchronization with Metasync.",
        copy=False
    )
    id_empresa = fields.Char(
        string='ID Empresa'
    )
    fecha_mod = fields.Datetime(
        string='Fecha Modificación'
    )
    codigo = fields.Char(
        string='Código'
    )
    estado = fields.Char(
        string='Estado'
    )

    # Datos físicos del vehículo
    bastidor = fields.Char(
        string='Bastidor'
    )
    matricula = fields.Char(
        string='Matrícula'
    )
    color = fields.Char(
        string='Color'
    )
    kilometraje = fields.Integer(
        string='Kilometraje'
    )
    anyo_vehiculo = fields.Integer(
        string='Año del vehículo'
    )
    codigo_motor = fields.Char(
        string='Código Motor'
    )
    codigo_cambio = fields.Char(
        string='Código Cambio'
    )
    observaciones = fields.Text(
        string='Observaciones'
    )

    # Datos de marca/modelo
    cod_marca = fields.Char(
        string='Código Marca'
    )
    nombre_marca = fields.Char(
        string='Nombre Marca'
    )
    cod_modelo = fields.Char(
        string='Código Modelo'
    )
    nombre_modelo = fields.Char(
        string='Nombre Modelo'
    )
    cod_version = fields.Char(
        string='Código Versión'
    )
    nombre_version = fields.Char(
        string='Nombre Versión'
    )
    tipo_version = fields.Char(
        string='Tipo Versión'
    )

    # Especificaciones técnicas
    combustible = fields.Char(
        string='Combustible'
    )
    puertas = fields.Integer(
        string='Puertas'
    )
    anyo_inicio = fields.Integer(
        string='Año Inicio'
    )
    anyo_fin = fields.Integer(
        string='Año Fin'
    )
    tipos_motor = fields.Char(
        string='Tipos Motor'
    )
    potencia_hp = fields.Float(
        string='Potencia HP'
    )
    potencia_kw = fields.Float(
        string='Potencia KW'
    )
    cilindrada = fields.Integer(
        string='Cilindrada'
    )
    transmision = fields.Char(
        string='Transmisión'
    )
    alimentacion = fields.Char(
        string='Alimentación'
    )
    num_marchas = fields.Integer(
        string='Número de marchas'
    )

    # Códigos adicionales
    rv_code = fields.Char(
        string='RV Code'
    )
    ktype = fields.Char(
        string='K Type'
    )

    # URLs de imágenes
    urls_imgs = fields.Text(
        string='URLs Imágenes'
    )

    img_urls_list = fields.Json(
        string='Lista de URLs Imágenes'
    )

    img_urls_list = fields.Json(
        string='Lista de URLs Imágenes',
        compute='_compute_img_urls_list',
        store=True
    )

    @api.depends('urls_imgs')
    def _compute_img_urls_list(self):
        for record in self:
            if record.urls_imgs:
                record.img_urls_list = [u.strip() for u in record.urls_imgs.splitlines() if u.strip()]
            else:
                record.img_urls_list = []

    def set_img_urls_list(self):
        for record in self:
            if record.urls_imgs:
                record.img_urls_list = [u.strip() for u in record.urls_imgs.splitlines() if u.strip()]
            else:
                record.img_urls_list = []

    image_ids = fields.One2many(
        'product.vehicle.image',
        'vehicle_id',
        string="Imágenes"
    )

    state = fields.Selection(
        [
            ('published', 'Published'),
            ('unpublished', 'Unpublished')
        ],
        compute='_compute_state',
        store=False, string="State"
    )

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

    @api.model
    def create(self, vals):
        """Override create para logging"""
        result = super().create(vals)
        print(f"Vehículo creado: {result.name} (ID Local: {result.id_local})")
        return result

    def write(self, vals):
        """Override write para logging"""
        result = super().write(vals)
        for vehicle in self:
            print(f"Vehículo actualizado: {vehicle.name} (ID Local: {vehicle.id_local})")
        return result

    def name_get(self):
        """Personalizar el nombre mostrado"""
        result = []
        for vehicle in self:
            if vehicle.id_local:
                name = f"{vehicle.name} (ID: {vehicle.id_local})"
            else:
                name = vehicle.name
            result.append((vehicle.id, name))
        return result

    @api.model
    def find_by_local_id(self, local_id):
        """Método auxiliar para buscar vehículo por ID local"""
        return self.search([('id_local', '=', local_id)], limit=1)

    @api.model
    def debug_search_by_local_id(self, local_id):
        """Método de debugging para buscar vehículo por ID local"""
        print(f"Buscando vehículo con id_local = {local_id}")
        vehicles = self.search([('id_local', '=', local_id)])
        print(f"Encontrados {len(vehicles)} vehículos")
        for vehicle in vehicles:
            print(f"  - ID: {vehicle.id}, Nombre: {vehicle.name}, ID Local: {vehicle.id_local}")
        return vehicles

    def get_vehicles_count_by_sync_status(self):
        """Obtener conteo de vehículos por estado"""
        total = self.search_count([])
        with_id = self.search_count([('id_local', '!=', False)])
        without_id = total - with_id
        return {
            'total': total,
            'with_metasync_id': with_id,
            'without_metasync_id': without_id
        }
