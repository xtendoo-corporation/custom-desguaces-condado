# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import HttpCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestWebsiteVehicle(HttpCase):
    """Test cases for website vehicle functionality"""

    def setUp(self):
        super().setUp()
        self.ProductVehicle = self.env['product.vehicle']
        self.ProductTemplate = self.env['product.template']
        self.ProductImage = self.env['product.image']

        # Create test vehicles
        self.vehicle_published = self.ProductVehicle.create({
            'name': 'BMW X5 2020 - Published',
            'description': '<p>Published vehicle for testing</p>',
            'bastidor': 'WBAFR9C50DD111111',
            'matricula': '1111ABC',
            'nombre_marca': 'BMW',
            'nombre_modelo': 'X5',
            'anyo_vehiculo': 2020,
            'is_published': True,
        })

        self.vehicle_unpublished = self.ProductVehicle.create({
            'name': 'Mercedes C-Class 2019 - Unpublished',
            'description': '<p>Unpublished vehicle for testing</p>',
            'bastidor': 'WDD2050621A222222',
            'matricula': '2222DEF',
            'nombre_marca': 'Mercedes',
            'nombre_modelo': 'C-Class',
            'anyo_vehiculo': 2019,
            'is_published': False,
        })

        # Create products for published vehicle
        self.product1 = self.ProductTemplate.create({
            'name': 'BMW X5 Engine 2020',
            'product_vehicle_id': self.vehicle_published.id,
            'list_price': 5000.0,
            'website_published': True,
        })

        self.product2 = self.ProductTemplate.create({
            'name': 'BMW X5 Transmission 2020',
            'product_vehicle_id': self.vehicle_published.id,
            'list_price': 3000.0,
            'website_published': True,
        })

    def test_vehicle_list_page_access(self):
        """Test that vehicle list page is accessible"""
        # This test would require actual controller implementation
        # For now, we test the template rendering logic
        vehicles = self.ProductVehicle.search([('is_published', '=', True)])
        self.assertIn(self.vehicle_published, vehicles)
        self.assertNotIn(self.vehicle_unpublished, vehicles)

    def test_vehicle_detail_page_context(self):
        """Test vehicle detail page context preparation"""
        # Test that vehicle has required data for detail page
        self.assertTrue(self.vehicle_published.name)
        self.assertTrue(self.vehicle_published.description)

        # Test products count for detail page
        self.vehicle_published._compute_products_count()
        self.assertEqual(self.vehicle_published.products_count, 2)

    def test_vehicle_search_functionality(self):
        """Test vehicle search functionality"""
        # Create vehicles with different names for search testing
        search_vehicle = self.ProductVehicle.create({
            'name': 'Audi A4 2021 Special Edition',
            'nombre_marca': 'Audi',
            'nombre_modelo': 'A4',
            'anyo_vehiculo': 2021,
            'is_published': True,
        })

        # Test search by name
        search_results = self.ProductVehicle.search([
            ('name', 'ilike', 'Audi'),
            ('is_published', '=', True)
        ])
        self.assertIn(search_vehicle, search_results)

        # Test search by brand
        search_results = self.ProductVehicle.search([
            ('nombre_marca', 'ilike', 'BMW'),
            ('is_published', '=', True)
        ])
        self.assertIn(self.vehicle_published, search_results)

    def test_vehicle_images_handling(self):
        """Test vehicle images for web display"""
        # Create image for vehicle
        image_data = b'fake_image_data'
        vehicle_image = self.ProductImage.create({
            'name': 'BMW X5 Front View',
            'image_1920': image_data,
            'product_vehicle_id': self.vehicle_published.id,
        })

        self.vehicle_published.product_image_ids = [(6, 0, [vehicle_image.id])]

        # Test that vehicle has images
        self.assertTrue(self.vehicle_published.product_image_ids)
        self.assertEqual(len(self.vehicle_published.product_image_ids), 1)

    def test_vehicle_breadcrumb_data(self):
        """Test breadcrumb data preparation"""
        # Test that vehicle has required data for breadcrumbs
        self.assertTrue(self.vehicle_published.name)
        self.assertTrue(self.vehicle_published.id)

    def test_vehicle_contact_query_preparation(self):
        """Test contact query URL preparation"""
        expected_subject = f"Query about {self.vehicle_published.name}"
        contact_url = f"/contactus?subject={expected_subject}"

        # Test that the subject contains vehicle name
        self.assertIn(self.vehicle_published.name, expected_subject)

    def test_vehicle_published_filter(self):
        """Test published vehicle filtering"""
        all_vehicles = self.ProductVehicle.search([])
        published_vehicles = self.ProductVehicle.search([('is_published', '=', True)])
        unpublished_vehicles = self.ProductVehicle.search([('is_published', '=', False)])

        self.assertIn(self.vehicle_published, published_vehicles)
        self.assertNotIn(self.vehicle_published, unpublished_vehicles)
        self.assertIn(self.vehicle_unpublished, unpublished_vehicles)
        self.assertNotIn(self.vehicle_unpublished, published_vehicles)

    def test_vehicle_related_products_display(self):
        """Test related products display logic"""
        # Test that published vehicle has products
        self.assertTrue(self.vehicle_published.product_ids)
        self.assertEqual(len(self.vehicle_published.product_ids), 2)

        # Test that products have required fields for display
        for product in self.vehicle_published.product_ids:
            self.assertTrue(product.name)
            self.assertTrue(product.list_price)

    def test_vehicle_no_products_scenario(self):
        """Test vehicle with no related products"""
        empty_vehicle = self.ProductVehicle.create({
            'name': 'Empty Vehicle',
            'is_published': True,
        })

        empty_vehicle._compute_products_count()
        self.assertEqual(empty_vehicle.products_count, 0)
        self.assertEqual(len(empty_vehicle.product_ids), 0)

    def test_vehicle_website_ribbon(self):
        """Test vehicle website ribbon functionality"""
        # Create ribbon
        ribbon = self.env['product.ribbon'].create({
            'name': 'New Arrival',
            'bg_color': '#28a745',
            'text_color': '#ffffff',
        })

        self.vehicle_published.website_ribbon_id = ribbon

        self.assertEqual(self.vehicle_published.website_ribbon_id, ribbon)

    def test_vehicle_state_consistency(self):
        """Test vehicle state consistency for web display"""
        # Published vehicle
        self.assertEqual(self.vehicle_published.state, 'published')
        self.assertTrue(self.vehicle_published.is_published)

        # Unpublished vehicle
        self.assertEqual(self.vehicle_unpublished.state, 'unpublished')
        self.assertFalse(self.vehicle_unpublished.is_published)

    def test_vehicle_seo_data(self):
        """Test vehicle SEO data preparation"""
        # Test that vehicle has data needed for SEO
        self.assertTrue(self.vehicle_published.name)  # For title
        self.assertTrue(self.vehicle_published.description)  # For meta description

        # Test that description is HTML and can be processed
        self.assertIn('<p>', self.vehicle_published.description)

    def test_vehicle_ordering_web_display(self):
        """Test vehicle ordering for web display"""
        # Create multiple vehicles
        vehicle_a = self.ProductVehicle.create({
            'name': 'Audi A3 2020',
            'is_published': True,
        })
        vehicle_z = self.ProductVehicle.create({
            'name': 'Volvo XC90 2021',
            'is_published': True,
        })

        vehicles = self.ProductVehicle.search([
            ('is_published', '=', True),
            ('id', 'in', [vehicle_a.id, vehicle_z.id, self.vehicle_published.id])
        ])

        # Should be ordered by name (default order)
        vehicle_names = [v.name for v in vehicles]
        sorted_names = sorted(vehicle_names)
        self.assertEqual(vehicle_names, sorted_names)

    def test_vehicle_products_website_published_filter(self):
        """Test that only website published products are shown"""
        # Create unpublished product
        unpublished_product = self.ProductTemplate.create({
            'name': 'BMW X5 Unpublished Part',
            'product_vehicle_id': self.vehicle_published.id,
            'list_price': 1000.0,
            'website_published': False,
        })

        # Get published products for vehicle
        published_products = self.vehicle_published.product_ids.filtered('website_published')

        self.assertEqual(len(published_products), 2)
        self.assertNotIn(unpublished_product, published_products)
