# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestProductVehicle(TransactionCase):
    """Test cases for product.vehicle model"""

    def setUp(self):
        super().setUp()
        self.ProductVehicle = self.env['product.vehicle']
        self.ProductTemplate = self.env['product.template']

        # Create test data
        self.test_vehicle = self.ProductVehicle.create({
            'name': 'Test Vehicle BMW X5 2020',
            'description': '<p>Test vehicle description</p>',
            'bastidor': 'WBAFR9C50DD123456',
            'matricula': '1234ABC',
            'color': 'Negro',
            'kilometraje': 50000,
            'anyo_vehiculo': 2020,
            'nombre_marca': 'BMW',
            'nombre_modelo': 'X5',
            'combustible': 'Diesel',
            'puertas': 5,
            'potencia_hp': 265.0,
            'potencia_kw': 195.0,
            'cilindrada': 2993,
            'transmision': 'Automática',
            'is_published': True,
        })

    def test_vehicle_creation(self):
        """Test basic vehicle creation"""
        self.assertTrue(self.test_vehicle.id)
        self.assertEqual(self.test_vehicle.name, 'Test Vehicle BMW X5 2020')
        self.assertEqual(self.test_vehicle.bastidor, 'WBAFR9C50DD123456')
        self.assertEqual(self.test_vehicle.anyo_vehiculo, 2020)
        self.assertTrue(self.test_vehicle.is_published)

    def test_vehicle_required_fields(self):
        """Test that required fields are validated"""
        with self.assertRaises(ValidationError):
            self.ProductVehicle.create({
                'description': 'Vehicle without name'
            })

    def test_vehicle_state_computation(self):
        """Test state computation based on is_published"""
        self.assertEqual(self.test_vehicle.state, 'published')

        self.test_vehicle.is_published = False
        self.assertEqual(self.test_vehicle.state, 'unpublished')

    def test_products_count_computation(self):
        """Test products count computation"""
        # Initially no products
        self.assertEqual(self.test_vehicle.products_count, 0)

        # Create products linked to vehicle
        product1 = self.ProductTemplate.create({
            'name': 'BMW X5 Engine 2020',
            'product_vehicle_id': self.test_vehicle.id,
            'list_price': 5000.0,
        })

        product2 = self.ProductTemplate.create({
            'name': 'BMW X5 Transmission 2020',
            'product_vehicle_id': self.test_vehicle.id,
            'list_price': 3000.0,
        })

        # Refresh and check count
        self.test_vehicle._compute_products_count()
        self.assertEqual(self.test_vehicle.products_count, 2)

    def test_website_publish_button(self):
        """Test website publish button functionality"""
        initial_state = self.test_vehicle.is_published

        # Toggle publish state
        self.test_vehicle.website_publish_button()
        self.assertEqual(self.test_vehicle.is_published, not initial_state)

        # Toggle back
        self.test_vehicle.website_publish_button()
        self.assertEqual(self.test_vehicle.is_published, initial_state)

    def test_vehicle_technical_specifications(self):
        """Test technical specifications fields"""
        vehicle = self.ProductVehicle.create({
            'name': 'Technical Test Vehicle',
            'potencia_hp': 300.0,
            'potencia_kw': 220.5,
            'cilindrada': 3500,
            'num_marchas': 8,
            'anyo_inicio': 2018,
            'anyo_fin': 2023,
        })

        self.assertEqual(vehicle.potencia_hp, 300.0)
        self.assertEqual(vehicle.potencia_kw, 220.5)
        self.assertEqual(vehicle.cilindrada, 3500)
        self.assertEqual(vehicle.num_marchas, 8)
        self.assertEqual(vehicle.anyo_inicio, 2018)
        self.assertEqual(vehicle.anyo_fin, 2023)

    def test_vehicle_metasync_fields(self):
        """Test Metasync integration fields"""
        vehicle = self.ProductVehicle.create({
            'name': 'Metasync Test Vehicle',
            'id_local': 'LOCAL_123',
            'id_empresa': 'EMP_456',
            'codigo': 'VEH_789',
            'estado': 'ACTIVE',
            'rv_code': 'RV123',
            'ktype': 'K456',
        })

        self.assertEqual(vehicle.id_local, 'LOCAL_123')
        self.assertEqual(vehicle.id_empresa, 'EMP_456')
        self.assertEqual(vehicle.codigo, 'VEH_789')
        self.assertEqual(vehicle.estado, 'ACTIVE')
        self.assertEqual(vehicle.rv_code, 'RV123')
        self.assertEqual(vehicle.ktype, 'K456')

    def test_vehicle_brand_model_info(self):
        """Test brand and model information fields"""
        vehicle = self.ProductVehicle.create({
            'name': 'Brand Model Test',
            'cod_marca': 'BMW',
            'nombre_marca': 'BMW',
            'cod_modelo': 'X5',
            'nombre_modelo': 'X5',
            'cod_version': 'xDrive30d',
            'nombre_version': 'xDrive30d',
            'tipo_version': 'SUV',
        })

        self.assertEqual(vehicle.cod_marca, 'BMW')
        self.assertEqual(vehicle.nombre_marca, 'BMW')
        self.assertEqual(vehicle.cod_modelo, 'X5')
        self.assertEqual(vehicle.nombre_modelo, 'X5')
        self.assertEqual(vehicle.cod_version, 'xDrive30d')
        self.assertEqual(vehicle.nombre_version, 'xDrive30d')
        self.assertEqual(vehicle.tipo_version, 'SUV')

    def test_vehicle_ordering(self):
        """Test that vehicles are ordered by name"""
        vehicle_a = self.ProductVehicle.create({'name': 'A Vehicle'})
        vehicle_z = self.ProductVehicle.create({'name': 'Z Vehicle'})
        vehicle_b = self.ProductVehicle.create({'name': 'B Vehicle'})

        vehicles = self.ProductVehicle.search([
            ('id', 'in', [vehicle_a.id, vehicle_z.id, vehicle_b.id])
        ])

        # Should be ordered by name
        self.assertEqual(vehicles[0].name, 'A Vehicle')
        self.assertEqual(vehicles[1].name, 'B Vehicle')
        self.assertEqual(vehicles[2].name, 'Z Vehicle')
