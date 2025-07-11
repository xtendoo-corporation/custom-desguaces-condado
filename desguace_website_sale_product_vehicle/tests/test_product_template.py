# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):
    """Test cases for product.template model extensions"""

    def setUp(self):
        super().setUp()
        self.ProductVehicle = self.env['product.vehicle']
        self.ProductTemplate = self.env['product.template']

        # Create test vehicle
        self.test_vehicle = self.ProductVehicle.create({
            'name': 'Test Vehicle for Products',
            'description': '<p>Vehicle for product testing</p>',
            'nombre_marca': 'Mercedes',
            'nombre_modelo': 'C-Class',
            'anyo_vehiculo': 2019,
        })

    def test_product_vehicle_relation(self):
        """Test product template vehicle relationship"""
        product = self.ProductTemplate.create({
            'name': 'Mercedes C-Class Door',
            'product_vehicle_id': self.test_vehicle.id,
            'list_price': 500.0,
        })

        self.assertEqual(product.product_vehicle_id, self.test_vehicle)
        self.assertIn(product, self.test_vehicle.product_ids)

    def test_search_get_detail_with_vehicle_filter(self):
        """Test search functionality with vehicle filter"""
        # Create products for different vehicles
        vehicle2 = self.ProductVehicle.create({
            'name': 'Another Test Vehicle',
            'nombre_marca': 'Audi',
            'nombre_modelo': 'A4',
        })

        product1 = self.ProductTemplate.create({
            'name': 'Mercedes Part',
            'product_vehicle_id': self.test_vehicle.id,
            'list_price': 100.0,
        })

        product2 = self.ProductTemplate.create({
            'name': 'Audi Part',
            'product_vehicle_id': vehicle2.id,
            'list_price': 200.0,
        })

        product3 = self.ProductTemplate.create({
            'name': 'Generic Part',
            'list_price': 50.0,
        })

        # Mock website context
        website = self.env['website'].browse(1)

        # Test search with vehicle filter
        options = {'vehicle': self.test_vehicle.id}
        result = self.ProductTemplate._search_get_detail(website, None, options)

        # Check that vehicle filter is added to domain
        domain = result['base_domain']
        vehicle_filter = [('product_vehicle_id', '=', self.test_vehicle.id)]
        self.assertIn(vehicle_filter[0], domain)

    def test_search_get_detail_without_vehicle_filter(self):
        """Test search functionality without vehicle filter"""
        website = self.env['website'].browse(1)
        options = {}

        result = self.ProductTemplate._search_get_detail(website, None, options)

        # Check that no vehicle filter is added when not specified
        domain = result['base_domain']
        vehicle_filters = [item for item in domain if isinstance(item, list) and len(item) == 3 and item[0] == 'product_vehicle_id']
        self.assertEqual(len(vehicle_filters), 0)

    def test_multiple_products_same_vehicle(self):
        """Test multiple products can belong to same vehicle"""
        products = []
        for i in range(5):
            product = self.ProductTemplate.create({
                'name': f'Mercedes Part {i+1}',
                'product_vehicle_id': self.test_vehicle.id,
                'list_price': 100.0 * (i+1),
            })
            products.append(product)

        # Refresh vehicle to get updated product count
        self.test_vehicle._compute_products_count()
        self.assertEqual(self.test_vehicle.products_count, 5)

        # Check all products are linked to vehicle
        for product in products:
            self.assertEqual(product.product_vehicle_id, self.test_vehicle)

    def test_product_without_vehicle(self):
        """Test products can exist without vehicle association"""
        product = self.ProductTemplate.create({
            'name': 'Generic Auto Part',
            'list_price': 25.0,
        })

        self.assertFalse(product.product_vehicle_id)

        # Should not affect any vehicle's product count
        self.test_vehicle._compute_products_count()
        self.assertEqual(self.test_vehicle.products_count, 0)

    def test_product_vehicle_change(self):
        """Test changing vehicle association of a product"""
        # Create second vehicle
        vehicle2 = self.ProductVehicle.create({
            'name': 'Second Test Vehicle',
            'nombre_marca': 'BMW',
            'nombre_modelo': 'X3',
        })

        # Create product initially linked to first vehicle
        product = self.ProductTemplate.create({
            'name': 'Transferable Part',
            'product_vehicle_id': self.test_vehicle.id,
            'list_price': 300.0,
        })

        # Verify initial state
        self.test_vehicle._compute_products_count()
        vehicle2._compute_products_count()
        self.assertEqual(self.test_vehicle.products_count, 1)
        self.assertEqual(vehicle2.products_count, 0)

        # Change vehicle association
        product.product_vehicle_id = vehicle2

        # Verify counts are updated
        self.test_vehicle._compute_products_count()
        vehicle2._compute_products_count()
        self.assertEqual(self.test_vehicle.products_count, 0)
        self.assertEqual(vehicle2.products_count, 1)

    def test_product_vehicle_field_index(self):
        """Test that product_vehicle_id field has index for performance"""
        field = self.ProductTemplate._fields['product_vehicle_id']
        self.assertTrue(field.index, "product_vehicle_id field should be indexed for performance")
