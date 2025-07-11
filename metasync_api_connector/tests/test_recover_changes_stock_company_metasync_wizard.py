from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from unittest.mock import patch, MagicMock
import json
from datetime import datetime
import base64


class TestRecoverChangesStockCompanyMetasyncWizard(TransactionCase):

    def setUp(self):
        super().setUp()

        # Configurar parámetros del sistema
        self.env['ir.config_parameter'].sudo().set_param('metasync.inventory.apikey', 'test_api_key_123')
        self.env['ir.config_parameter'].sudo().set_param('metasync.id_empresa', 'test_empresa_456')

        # Crear el wizard
        self.wizard = self.env['recover.changes.stock.company.metasync.wizard'].create({
            'fecha': datetime(2024, 1, 30, 15, 42, 33),
            'lastid': '100',
            'offset': 5
        })

        # Datos de prueba simulando respuesta de API
        self.mock_api_response = {
            'vehiculos': [
                {
                    'idLocal': 12345,
                    'idEmpresa': 'EMP001',
                    'codigo': 'VEH001',
                    'estado': 'Activo',
                    'bastidor': 'VF1234567890',
                    'matricula': '1234ABC',
                    'color': 'Azul',
                    'kilometraje': 150000,
                    'anyoVehiculo': 2018,
                    'codigoMotor': 'MOT123',
                    'codigoCambio': 'CAM456',
                    'observaciones': 'Vehículo en buen estado',
                    'codMarca': 'REN',
                    'nombreMarca': 'Renault',
                    'codModelo': 'CLIO',
                    'nombreModelo': 'Clio',
                    'codVersion': 'TCE90',
                    'nombreVersion': 'TCE 90',
                    'tipoVersion': 'Gasolina',
                    'combustible': 'Gasolina',
                    'puertas': 5,
                    'anyoInicio': 2016,
                    'anyoFin': 2020,
                    'tiposMotor': 'TCE',
                    'potenciaHP': 90.5,
                    'potenciaKw': 67.2,
                    'cilindrada': 898,
                    'transmision': 'Manual',
                    'alimentacion': 'Inyección',
                    'numMarchas': 5,
                    'rvCode': 'RV123',
                    'ktype': 'KT456',
                    'urlsImgs': ['https://example.com/img1', 'https://example.com/img2'],
                    'fechaMod': '2024-01-30T15:42:33'
                }
            ],
            'piezas': [
                {
                    'refLocal': 'REF001',
                    'descripcionArticulo': 'Faro delantero izquierdo',
                    'idVehiculo': 12345,
                    'precio': 15750,  # En centavos
                    'peso': 2.5,
                    'refPrincipal': 'PRIN001',
                    'codVersion': 'VER001',
                    'codArticulo': 'ART001',
                    'anyoStock': '2024',
                    'ubicacion': 1,  # Almacenada
                    'observaciones': 'Pieza original',
                    'reserva': 'No',
                    'tipoMaterial': 0,  # Revisado
                    'codAlmacen': 'ALM001',
                    'codFamilia': 'FAR',
                    'descripcionFamilia': 'Faros',
                    'urlsImgs': ['https://example.com/pieza1'],
                    'fechaMod': '2024-01-30T15:42:33'
                }
            ]
        }

    def test_configuration_missing_api_key(self):
        """Test que falla cuando falta la API key"""
        # Eliminar parámetro
        self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'metasync.inventory.apikey')
        ]).unlink()

        with self.assertRaises(UserError) as cm:
            self.wizard.recuperar_cambios_almacen_empresa_metasync()

        self.assertIn("metasync.inventory.apikey", str(cm.exception))

    def test_configuration_missing_empresa_id(self):
        """Test que falla cuando falta el ID de empresa"""
        # Eliminar parámetro
        self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'metasync.id_empresa')
        ]).unlink()

        with self.assertRaises(UserError) as cm:
            self.wizard.recuperar_cambios_almacen_empresa_metasync()

        self.assertIn("metasync.id_empresa", str(cm.exception))

    @patch('requests.get')
    def test_vehicle_creation_complete(self, mock_get):
        """Test creación completa de vehículo con todos los datos"""
        # Mock de la respuesta HTTP
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Ejecutar el wizard
        result = self.wizard.recuperar_cambios_almacen_empresa_metasync()

        # Verificar que se creó el vehículo
        vehicle = self.env['product.vehicle'].search([('id_local', '=', '12345')])
        self.assertTrue(vehicle, "El vehículo debería haberse creado")

        # Verificar todos los campos del vehículo
        self.assertEqual(vehicle.name, 'Renault Clio TCE 90')
        self.assertEqual(vehicle.id_local, '12345')
        self.assertEqual(vehicle.id_empresa, 'EMP001')
        self.assertEqual(vehicle.codigo, 'VEH001')
        self.assertEqual(vehicle.estado, 'Activo')
        self.assertEqual(vehicle.bastidor, 'VF1234567890')
        self.assertEqual(vehicle.matricula, '1234ABC')
        self.assertEqual(vehicle.color, 'Azul')
        self.assertEqual(vehicle.kilometraje, 150000)
        self.assertEqual(vehicle.anyo_vehiculo, 2018)
        self.assertEqual(vehicle.codigo_motor, 'MOT123')
        self.assertEqual(vehicle.codigo_cambio, 'CAM456')
        self.assertEqual(vehicle.observaciones, 'Vehículo en buen estado')
        self.assertEqual(vehicle.cod_marca, 'REN')
        self.assertEqual(vehicle.nombre_marca, 'Renault')
        self.assertEqual(vehicle.cod_modelo, 'CLIO')
        self.assertEqual(vehicle.nombre_modelo, 'Clio')
        self.assertEqual(vehicle.cod_version, 'TCE90')
        self.assertEqual(vehicle.nombre_version, 'TCE 90')
        self.assertEqual(vehicle.tipo_version, 'Gasolina')
        self.assertEqual(vehicle.combustible, 'Gasolina')
        self.assertEqual(vehicle.puertas, 5)
        self.assertEqual(vehicle.anyo_inicio, 2016)
        self.assertEqual(vehicle.anyo_fin, 2020)
        self.assertEqual(vehicle.tipos_motor, 'TCE')
        self.assertEqual(vehicle.potencia_hp, 90.5)
        self.assertEqual(vehicle.potencia_kw, 67.2)
        self.assertEqual(vehicle.cilindrada, 898)
        self.assertEqual(vehicle.transmision, 'Manual')
        self.assertEqual(vehicle.alimentacion, 'Inyección')
        self.assertEqual(vehicle.num_marchas, 5)
        self.assertEqual(vehicle.rv_code, 'RV123')
        self.assertEqual(vehicle.ktype, 'KT456')
        self.assertEqual(vehicle.urls_imgs, 'https://example.com/img1, https://example.com/img2')
        self.assertTrue(vehicle.website_published)

        # Verificar fecha de modificación
        expected_date = datetime(2024, 1, 30, 15, 42, 33)
        self.assertEqual(vehicle.fecha_mod, expected_date)

    @patch('requests.get')
    def test_piece_creation_complete(self, mock_get):
        """Test creación completa de pieza con todos los datos"""
        # Mock de la respuesta HTTP
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock para la imagen
        with patch.object(self.wizard, 'fetch_image') as mock_fetch:
            mock_fetch.return_value = base64.b64encode(b'fake_image_data')

            # Ejecutar el wizard
            result = self.wizard.recuperar_cambios_almacen_empresa_metasync()

        # Verificar que se creó la pieza
        piece = self.env['product.template'].search([('default_code', '=', 'REF001')])
        self.assertTrue(piece, "La pieza debería haberse creado")

        # Verificar todos los campos de la pieza
        self.assertEqual(piece.name, 'Faro delantero izquierdo')
        self.assertEqual(piece.default_code, 'REF001')
        self.assertEqual(piece.list_price, 157.50)  # 15750 centavos = 157.50 euros
        self.assertEqual(piece.weight, 2.5)
        self.assertEqual(piece.principal_ref, 'PRIN001')
        self.assertEqual(piece.version_code, 'VER001')
        self.assertEqual(piece.article_code, 'ART001')
        self.assertEqual(piece.stock_year, '2024')
        self.assertEqual(piece.location, 'Almacenada')
        self.assertEqual(piece.observations, 'Pieza original')
        self.assertEqual(piece.reserve, 'No')
        self.assertEqual(piece.material_type, 'Revisado')
        self.assertEqual(piece.cod_almacen, 'ALM001')
        self.assertEqual(piece.modification_date, '2024-01-30 15:42:33')
        self.assertTrue(piece.website_published)
        self.assertTrue(piece.image_1920, "La pieza debería tener imagen")

    @patch('requests.get')
    def test_piece_vehicle_relationship(self, mock_get):
        """Test relación entre pieza y vehículo"""
        # Mock de la respuesta HTTP
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock para la imagen
        with patch.object(self.wizard, 'fetch_image') as mock_fetch:
            mock_fetch.return_value = base64.b64encode(b'fake_image_data')

            # Ejecutar el wizard
            result = self.wizard.recuperar_cambios_almacen_empresa_metasync()

        # Verificar que se crearon ambos registros
        vehicle = self.env['product.vehicle'].search([('id_local', '=', '12345')])
        piece = self.env['product.template'].search([('default_code', '=', 'REF001')])

        self.assertTrue(vehicle, "El vehículo debería existir")
        self.assertTrue(piece, "La pieza debería existir")

        # Verificar la relación
        self.assertEqual(piece.product_vehicle_id.id, vehicle.id,
                         "La pieza debería estar relacionada con el vehículo")

    @patch('requests.get')
    def test_category_creation(self, mock_get):
        """Test creación de categorías"""
        # Mock de la respuesta HTTP
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock para la imagen
        with patch.object(self.wizard, 'fetch_image') as mock_fetch:
            mock_fetch.return_value = base64.b64encode(b'fake_image_data')

            # Ejecutar el wizard
            result = self.wizard.recuperar_cambios_almacen_empresa_metasync()

        # Verificar categoría interna
        category = self.env['product.category'].search([('default_code', '=', 'FAR')])
        self.assertTrue(category, "La categoría interna debería haberse creado")
        self.assertEqual(category.name, 'Faros')

        # Verificar categorías públicas
        public_categ_vehiculos = self.env['product.public.category'].search([('name', '=', 'Vehículos')])
        public_categ_faros = self.env['product.public.category'].search([('name', '=', 'Faros')])

        self.assertTrue(public_categ_vehiculos, "La categoría pública 'Vehículos' debería existir")
        self.assertTrue(public_categ_faros, "La categoría pública 'Faros' debería existir")
        self.assertEqual(public_categ_faros.parent_id, public_categ_vehiculos)

    @patch('requests.get')
    def test_vehicle_update_existing(self, mock_get):
        """Test actualización de vehículo existente"""
        # Crear vehículo existente
        existing_vehicle = self.env['product.vehicle'].create({
            'name': 'Vehículo Anterior',
            'id_local': '12345',
            'estado': 'Inactivo'
        })

        # Mock de la respuesta HTTP
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Ejecutar el wizard
        result = self.wizard.recuperar_cambios_almacen_empresa_metasync()

        # Verificar que se actualizó el vehículo existente
        existing_vehicle.refresh()
        self.assertEqual(existing_vehicle.name, 'Renault Clio TCE 90')
        self.assertEqual(existing_vehicle.estado, 'Activo')

        # Verificar que solo hay un vehículo con ese ID
        vehicles = self.env['product.vehicle'].search([('id_local', '=', '12345')])
        self.assertEqual(len(vehicles), 1, "Solo debería haber un vehículo con ese ID")

    @patch('requests.get')
    def test_piece_update_existing(self, mock_get):
        """Test actualización de pieza existente"""
        # Crear pieza existente
        existing_piece = self.env['product.template'].create({
            'name': 'Pieza Anterior',
            'default_code': 'REF001',
            'list_price': 100.0
        })

        # Mock de la respuesta HTTP
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock para la imagen
        with patch.object(self.wizard, 'fetch_image') as mock_fetch:
            mock_fetch.return_value = base64.b64encode(b'fake_image_data')

            # Ejecutar el wizard
            result = self.wizard.recuperar_cambios_almacen_empresa_metasync()

        # Verificar que se actualizó la pieza existente
        existing_piece.refresh()
        self.assertEqual(existing_piece.name, 'Faro delantero izquierdo')
        self.assertEqual(existing_piece.list_price, 157.50)

        # Verificar que solo hay una pieza con ese código
        pieces = self.env['product.template'].search([('default_code', '=', 'REF001')])
        self.assertEqual(len(pieces), 1, "Solo debería haber una pieza con ese código")

    @patch('requests.get')
    def test_date_parsing_invalid_format(self, mock_get):
        """Test manejo de fechas con formato inválido"""
        # Datos con fecha inválida
        invalid_data = self.mock_api_response.copy()
        invalid_data['vehiculos'][0]['fechaMod'] = 'fecha_invalida'

        mock_response = MagicMock()
        mock_response.json.return_value = invalid_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Ejecutar el wizard
        result = self.wizard.recuperar_cambios_almacen_empresa_metasync()

        # Verificar que el vehículo se creó sin fecha
        vehicle = self.env['product.vehicle'].search([('id_local', '=', '12345')])
        self.assertTrue(vehicle, "El vehículo debería haberse creado")
        self.assertFalse(vehicle.fecha_mod, "La fecha debería estar vacía")

    @patch('requests.get')
    def test_api_request_error(self, mock_get):
        """Test manejo de errores en la API"""
        # Simular error de conexión
        mock_get.side_effect = Exception("Error de conexión")

        with self.assertRaises(UserError) as cm:
            self.wizard.recuperar_cambios_almacen_empresa_metasync()

        self.assertIn("Error inesperado", str(cm.exception))

    @patch('requests.get')
    def test_statistics_generation(self, mock_get):
        """Test generación de estadísticas"""
        # Mock de la respuesta HTTP
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock para la imagen
        with patch.object(self.wizard, 'fetch_image') as mock_fetch:
            mock_fetch.return_value = base64.b64encode(b'fake_image_data')

            # Ejecutar el wizard
            result = self.wizard.recuperar_cambios_almacen_empresa_metasync()

        # Verificar el resultado
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(result['params']['type'], 'success')

        # Verificar que el mensaje contiene estadísticas
        message = result['params']['message']
        self.assertIn('Vehículos', message)
        self.assertIn('Piezas', message)
        self.assertIn('creados: 1', message)

    def test_safe_conversion_functions(self):
        """Test funciones de conversión segura"""
        # Test datos del vehículo con valores problemáticos
        problematic_data = {
            'idLocal': 12345,
            'kilometraje': '',
            'anyoVehiculo': None,
            'puertas': 'abc',
            'potenciaHP': '90.5',
            'potenciaKw': False,
            'cilindrada': '898'
        }

        vehicle_result, status = self.wizard._process_vehicle(problematic_data)

        # Verificar que se manejaron correctamente los valores problemáticos
        self.assertEqual(vehicle_result.kilometraje, 0)
        self.assertEqual(vehicle_result.anyo_vehiculo, 0)
        self.assertEqual(vehicle_result.puertas, 0)
        self.assertEqual(vehicle_result.potencia_hp, 90.5)
        self.assertEqual(vehicle_result.potencia_kw, 0.0)
        self.assertEqual(vehicle_result.cilindrada, 898)

        # El vehículo debería crearse exitosamente
        self.assertEqual(status, 'created')

    def tearDown(self):
        """Limpiar después de cada test"""
        # Limpiar registros creados
        self.env['product.vehicle'].search([('id_local', '=', '12345')]).unlink()
        self.env['product.template'].search([('default_code', '=', 'REF001')]).unlink()
        self.env['product.category'].search([('default_code', '=', 'FAR')]).unlink()
        self.env['product.public.category'].search([('name', 'in', ['Vehículos', 'Faros'])]).unlink()

        super().tearDown()
