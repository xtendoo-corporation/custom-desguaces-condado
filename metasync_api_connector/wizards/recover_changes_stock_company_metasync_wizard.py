from PIL.ImageChops import offset

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import requests
from datetime import datetime


class RecoverChangesStockCompanyMetasyncWizard(models.TransientModel):
    _name = 'recover.changes.stock.company.metasync.wizard'
    _description = 'Recuperar Cambios Stock Company Metasync'

    fecha = fields.Datetime(string='Fecha', required=True, default=fields.Datetime.now)
    lastid = fields.Char(string='Last ID', required=True, default="0")
    offset = fields.Integer(string='Offset', required=True, default=10)

    def recuperar_cambios_almacen_empresa_metasync(self):
        self.ensure_one()
        api_key = self.env['ir.config_parameter'].sudo().get_param('metasync.inventory.apikey', default=None)
        if not api_key:
            raise UserError(
                "No está bien configurado el parámetro 'metasync.inventory.apikey' o no es correcto.")
        idempresa = self.env['ir.config_parameter'].sudo().get_param('metasync.id_empresa', default=None)
        if not idempresa:
            raise UserError(
                "No está bien configurado el parámetro 'metasync.inventory.idempresa' o no es correcto.")
        print("Fecha: ", self.fecha.strftime('%d/%m/%Y %H:%M:%S'))
        headers = {
            'apiKey': api_key,
            'fecha': self.fecha.strftime('%d/%m/%Y %H:%M:%S'),
            'lastid': self.lastid,
            'offset': str(self.offset),
            'idempresa': idempresa
        }
        situacion_map = {
            0: "En Proceso de Desmontaje",
            1: "Almacenada",
            2: "Con Incidencia",
            3: "En Reparto",
            4: "En Control de Calidad",
            5: "Desechada",
            6: "En Mostrador",
            7: "Montada Revisada",
            8: "Vendida",
            9: "Situación Desconocida"
        }
        type_material_map = {
            0: "Revisado",
            1: "Nuevo",
            2: "De segunda mano",
            3: "Reparado",
        }
        try:
            response = requests.get('https://apis.metasync.com/Almacen/RecuperarCambiosCanalEmpresa', headers=headers)
            response.raise_for_status()  # Lanza un error si la respuesta no es 200
            # Acceder a las piezas
            if len(response.json()['piezas']) == 0:
                print("No hay piezas")
            else:
                for pieza in response.json()['piezas']:
                    print('---')
                    # print(f"ID Empresa: {pieza['idEmpresa']}")
                    # print(f"Referencia local: {pieza['refLocal']}")
                    print(f"ID Vehículo: {pieza['idVehiculo']}")
                    # print(f"Código Familia: {pieza['codFamilia']}")
                    # print(f"Descripción Familia: {pieza['descripcionFamilia']}")
                    # print(f"Código Artículo: {pieza['codArticulo']}")
                    # print(f"Descripción del artículo: {pieza['descripcionArticulo']}")
                    # print(f"Código Versión: {pieza['codVersion']}")
                    # print(f"Referencia Principal: {pieza['refPrincipal']}")
                    # print(f"Precio: {pieza['precio']}")
                    # print(f"Año Stock: {pieza['anyoStock']}")
                    # print(f"Peso: {pieza['peso']}")
                    ubicacion_texto = situacion_map.get(pieza['ubicacion'], "Situación Desconocida")
                    # print(f"Ubicación: {ubicacion_texto}")
                    # print(f"Observaciones: {pieza['observaciones']}")
                    # print(f"Reserva: {pieza['reserva']}")
                    tipo_material_texto = type_material_map.get(pieza['tipoMaterial'], "Tipo Desconocido")
                    # print(f"Tipo Material: {tipo_material_texto}")
                    print(f"Imagen/es:")
                    for url in pieza['urlsImgs']:
                        url = url + ".jpeg"
                        print(f"- URL: {url}")
                    # print(f"Fecha de modificación: {pieza['fechaMod']}")
                    date_str = pieza['fechaMod']
                    date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                    formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"Fecha de modificación: {formatted_date}")
                    print(f"Código Almacén: {pieza['codAlmacen']}")
                    print('---')
                    image_data = None
                    if pieza['urlsImgs']:
                        first_image_url = pieza['urlsImgs'][0] + ".jpeg"
                        image_data = self.fetch_image(first_image_url)
                    is_product = self.env['product.product'].search([('default_code', '=', pieza['refLocal'])])
                    if is_product:
                        print(f"El producto {pieza['descripcionArticulo']} ya existe en la base de datos")
                        is_product.write({
                            'name': pieza['descripcionArticulo'],
                            'list_price': pieza['precio'] / 100,
                            'weight': pieza['peso'],
                            'image_1920': image_data,
                            'principal_ref': pieza['refPrincipal'],
                            # 'vehicle_id': pieza['idVehiculo'],
                            'version_code': pieza['codVersion'],
                            'article_code': pieza['codArticulo'],
                            'stock_year': pieza['anyoStock'],
                            'location': ubicacion_texto,
                            'observations': pieza['observaciones'],
                            'reserve': pieza['reserva'],
                            'material_type': tipo_material_texto,
                            'modification_date': formatted_date,
                            'cod_almacen': pieza['codAlmacen'],
                        })
                    else:
                        is_category = self.env['product.category'].search([('default_code', '=', pieza['codFamilia'])])
                        if is_category:
                            print(f"La categoría {pieza['descripcionFamilia']} ya existe en la base de datos")
                            category = is_category
                        else:
                            print(f"Creando la categoría {pieza['descripcionFamilia']}:")
                            category = self.env['product.category'].create({
                                'name': pieza['descripcionFamilia'],
                                'default_code': pieza['codFamilia'],
                                'parent_id': 1,
                            })
                            print(f"Categoría {category.name} creada")

                        # Primero, busca o crea la categoría padre de vehículos
                        vehiculos_public_category = self.env['product.public.category'].search([
                            ('name', '=', 'Vehículos')
                        ], limit=1)

                        # Para la categoría padre de vehículos
                        if not vehiculos_public_category:
                            vehiculos_public_category = self.env['product.public.category'].create({
                                'name': 'Vehículos',
                                'sequence': 1
                            })

                        real_public_category = self.env['product.public.category'].search([
                            ('name', '=', pieza['descripcionFamilia'])
                        ], limit=1)
                        if not real_public_category:
                            real_public_category = self.env['product.public.category'].create({
                                'name': pieza['descripcionFamilia'],
                                'parent_id': vehiculos_public_category.id,  # Establecemos la jerarquía
                                'sequence': 10,  # Añadimos secuencia
                            })

                        # Al crear el producto, asignar ambas categorías públicas
                        public_categ_ids = [(6, 0, [vehiculos_public_category.id, real_public_category.id])]

                        print(f"Creando el producto {pieza['descripcionArticulo']}:")
                        product = self.env['product.product'].create({
                            'name': pieza['descripcionArticulo'],
                            'default_code': pieza['refLocal'],
                            'categ_id': category.id,
                            'list_price': pieza['precio'] / 100,
                            'weight': pieza['peso'],
                            'image_1920': image_data,
                            'principal_ref': pieza['refPrincipal'],
                            'vehicle_id': pieza['idVehiculo'],
                            'version_code': pieza['codVersion'],
                            'article_code': pieza['codArticulo'],
                            'stock_year': pieza['anyoStock'],
                            'location': ubicacion_texto,
                            'observations': pieza['observaciones'],
                            'reserve': pieza['reserva'],
                            'material_type': tipo_material_texto,
                            'modification_date': formatted_date,
                            'cod_almacen': pieza['codAlmacen'],
                            'public_categ_ids': public_categ_ids,
                            'website_published': True,
                        })
                    # Acceder a los vehículos
                if len(response.json()['vehiculos']) == 0:
                    print("No hay vehículos")
                else:
                    print('VEHÍCULOS')
                    for vehiculo in response.json()['vehiculos']:
                        print('---')
                        print(f"ID local: {vehiculo['idLocal']}")
                        print(f"ID Empresa: {vehiculo['idEmpresa']}")
                        print(f"Fecha de modificación: {vehiculo['fechaMod']}")
                        print(f"Código: {vehiculo['codigo']}")
                        print(f"Estado: {vehiculo['estado']}")
                        print(f"Bastidor: {vehiculo['bastidor']}")
                        print(f"Matrícula: {vehiculo['matricula']}")
                        print(f"Color: {vehiculo['color']}")
                        print(f"Kilometraje: {vehiculo['kilometraje']}")
                        print(f"Año del vehículo: {vehiculo['anyoVehiculo']}")
                        print(f"Código Motor: {vehiculo['codigoMotor']}")
                        print(f"Código Cambio: {vehiculo['codigoCambio']}")
                        print(f"Observaciones: {vehiculo['observaciones']}")
                        print(f"Imagen/es:")
                        for url in vehiculo['urlsImgs']:
                            print(f"- URL: {url}")
                        print(f"Código Marca: {vehiculo['codMarca']}")
                        print(f"Nombre Marca: {vehiculo['nombreMarca']}")
                        print(f"Código Modelo: {vehiculo['codModelo']}")
                        print(f"Nombre Modelo: {vehiculo['nombreModelo']}")
                        print(f"Código Versión: {vehiculo['codVersion']}")
                        print(f"Nombre Versión: {vehiculo['nombreVersion']}")
                        print(f"Tipo Versión: {vehiculo['tipoVersion']}")
                        print(f"Combustible: {vehiculo['combustible']}")
                        print(f"Puertas: {vehiculo['puertas']}")
                        print(f"Año Inicio: {vehiculo['anyoInicio']}")
                        print(f"Año Fin: {vehiculo['anyoFin']}")
                        print(f"Tipos Motor: {vehiculo['tiposMotor']}")
                        print(f"Potencia HP: {vehiculo['potenciaHP']}")
                        print(f"Potencia KW: {vehiculo['potenciaKw']}")
                        print(f"Cilindrada: {vehiculo['cilindrada']}")
                        print(f"Transmisión: {vehiculo['transmision']}")
                        print(f"Alimentación: {vehiculo['alimentacion']}")
                        print(f"Número de marchas: {vehiculo['numMarchas']}")
                        print(f"RV Code: {vehiculo['rvCode']}")
                        print(f"K Type: {vehiculo['ktype']}")
                        print('---')

                        image_data = None
                        if vehiculo['urlsImgs']:
                            first_image_url = vehiculo['urlsImgs'][0] + ".jpeg"
                            image_data = self.fetch_image(first_image_url)
                        # modification_date = self.parse_date(vehiculo['fechaMod'])
                        name = f"{vehiculo['nombreMarca']} {vehiculo['nombreModelo']}" if vehiculo['nombreMarca'] and \
                                                                                          vehiculo[
                                                                                              'nombreModelo'] else "Vehiculo test"
                        #                                <tr><td>ID local</td><td>{vehiculo['idLocal']}</td></tr>
                        #                                <tr><td>ID Empresa</td><td>{vehiculo['idEmpresa']}</td></tr>
                        #                                <tr><td>Fecha de modificación</td><td>{modification_date}</td></tr>
                        # website_description = f"""
                        #    <table>
                        #        <tr><td>Código</td><td>{vehiculo['codigo']}</td></tr>
                        #        <tr><td>Estado</td><td>{vehiculo['estado']}</td></tr>
                        #        <tr><td>Bastidor</td><td>{vehiculo['bastidor']}</td></tr>
                        #        <tr><td>Matrícula</td><td>{vehiculo['matricula']}</td></tr>
                        #        <tr><td>Color</td><td>{vehiculo['color']}</td></tr>
                        #        <tr><td>Kilometraje</td><td>{vehiculo['kilometraje']}</td></tr>
                        #        <tr><td>Año del vehículo</td><td>{vehiculo['anyoVehiculo']}</td></tr>
                        #        <tr><td>Código Motor</td><td>{vehiculo['codigoMotor']}</td></tr>
                        #        <tr><td>Código Cambio</td><td>{vehiculo['codigoCambio']}</td></tr>
                        #        <tr><td>Observaciones</td><td>{vehiculo['observaciones']}</td></tr>
                        #        <tr><td>Código Marca</td><td>{vehiculo['codMarca']}</td></tr>
                        #        <tr><td>Código Modelo</td><td>{vehiculo['codModelo']}</td></tr>
                        #        <tr><td>Código Versión</td><td>{vehiculo['codVersion']}</td></tr>
                        #        <tr><td>Nombre Versión</td><td>{vehiculo['nombreVersion']}</td></tr>
                        #        <tr><td>Tipo Versión</td><td>{vehiculo['tipoVersion']}</td></tr>
                        #        <tr><td>Combustible</td><td>{vehiculo['combustible']}</td></tr>
                        #        <tr><td>Puertas</td><td>{vehiculo['puertas']}</td></tr>
                        #        <tr><td>Año Inicio</td><td>{vehiculo['anyoInicio']}</td></tr>
                        #        <tr><td>Año Fin</td><td>{vehiculo['anyoFin']}</td></tr>
                        #        <tr><td>Tipos Motor</td><td>{vehiculo['tiposMotor']}</td></tr>
                        #        <tr><td>Potencia HP</td><td>{vehiculo['potenciaHP']}</td></tr>
                        #        <tr><td>Potencia KW</td><td>{vehiculo['potenciaKw']}</td></tr>
                        #        <tr><td>Cilindrada</td><td>{vehiculo['cilindrada']}</td></tr>
                        #        <tr><td>Transmisión</td><td>{vehiculo['transmision']}</td></tr>
                        #        <tr><td>Alimentación</td><td>{vehiculo['alimentacion']}</td></tr>
                        #        <tr><td>Número de marchas</td><td>{vehiculo['numMarchas']}</td></tr>
                        #        <tr><td>RV Code</td><td>{vehiculo['rvCode']}</td></tr>
                        #        <tr><td>K Type</td><td>{vehiculo['ktype']}</td></tr>
                        #    </table>
                        #    """
                        filtered_vehiculo = {k: v for k, v in vehiculo.items() if
                                             v not in [0, None, '', []] and k not in ['idLocal', 'idEmpresa',
                                                                                      'urlsImgs']}

                        # Construct the website description
                        website_description = """
                            <style>
                                .product-card {
                                    max-width: 500px;
                                    font-family: Arial, sans-serif;
                                    border-radius: 10px;
                                    padding: 20px;
                                    background-color: #fff;
                                    box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
                                }
                                .product-card h2 {
                                    font-size: 20px;
                                    font-weight: bold;
                                    margin-bottom: 15px;
                                }
                                .product-card table {
                                    width: 100%;
                                    border-collapse: collapse;
                                }
                                .product-card td {
                                    padding: 8px 0;
                                    border-bottom: 1px solid #ddd;
                                }
                                .product-card td:first-child {
                                    font-weight: bold;
                                    width: 40%;
                                }
                                .product-card td:last-child {
                                    text-align: right;
                                    color: #333;
                                }
                            </style>

                            <div class="product-card">
                                <h2>Ficha del producto</h2>
                                <table>
                        """

                        for key, value in filtered_vehiculo.items():
                            website_description += f"""
                                    <tr>
                                        <td>{key.replace("_", " ").capitalize()}</td>
                                        <td>{value}</td>
                                    </tr>
                            """

                        website_description += """
                                </table>
                            </div>
                        """

                        is_category = self.env['product.category'].search([
                            ('default_code', '=', 'VEH'),
                            ('name', '=', 'Vehículos')
                        ])
                        if is_category:
                            print(f"La categoría Vehículos ya existe en la base de datos")
                            category = is_category
                        else:
                            print(f"Creando la categoría Vehículos:")
                            category = self.env['product.category'].create({
                                'name': 'Vehículos',
                                'default_code': 'VEH',
                                'parent_id': 1,
                            })
                            print(f"Categoría {category.name} creada")

                        if not category:
                            raise UserError("La categoría 'Vehículos' no se ha podido crear.")

                        # Primero, busca o crea la categoría padre de vehículos
                        vehiculos_public_category = self.env['product.public.category'].search([
                            ('name', '=', 'Vehículos')
                        ], limit=1)

                        if not vehiculos_public_category:
                            vehiculos_public_category = self.env['product.public.category'].create({
                                'name': 'Vehículos',
                                'sequence': 1,
                            })

                        # Luego, crea la subcategoría usando vehiculos_public_category como padre
                        existing_category = self.env['product.public.category'].search([
                            ('name', '=', name),
                            ('idLocal', '=', vehiculo['idLocal']),
                            ('idEmpresa', '=', vehiculo['idEmpresa'])
                        ], limit=1)

                        print(f"Existing category: {existing_category}")
                        if not existing_category:
                            existing_category = self.env['product.public.category'].create({
                                'name': name,
                                'idLocal': vehiculo['idLocal'],
                                'idEmpresa': vehiculo['idEmpresa'],
                                'parent_id': vehiculos_public_category.id,
                                'image_1920': image_data,
                                'website_description': website_description,
                                'sequence': 10
                            })
                        else:
                            print(f"Updating category: {existing_category.name}")
                            existing_category.write({
                                'image_1920': image_data,
                                'website_description': website_description,
                            })

                        image_data_vehicle = None
                        if vehiculo['urlsImgs']:
                            first_image_url = vehiculo['urlsImgs'][0] + ".jpeg"
                            image_data_vehicle = self.fetch_image(first_image_url)
                        print(f"Creating product with reference {vehiculo['idLocal']}")

                        if not existing_category or not existing_category.id:
                            raise UserError("La categoría del vehículo no se ha creado correctamente.")

                        existing_product = self.env['product.template'].search([
                            ('default_code', '=', vehiculo['idLocal'])
                        ], limit=1)

                        if existing_product:
                            print(f"Actualizando producto existente: {existing_product.name}")
                            existing_product.write({
                                'image_1920': image_data_vehicle,
                                'public_categ_ids': [(6, 0, [existing_category.id])],
                                'website_published': True,
                                'name': name,
                                'is_vehicle': True,  # <- Actualiza también si ya existe
                            })
                        else:
                            print(f"Creando producto nuevo para el vehículo: {name}")
                            self.env['product.template'].create({
                                'name': name,
                                'default_code': vehiculo['idLocal'],
                                'image_1920': image_data_vehicle,
                                'purchase_ok': False,
                                'sale_ok': False,
                                'website_published': True,
                                'list_price': 0,
                                'categ_id': category.id,
                                'is_vehicle': True,  # <- Aquí se indica que es un vehículo
                            })

                        product_templates = self.env['product.template'].search([
                            ('vehicle_id', '=', vehiculo['idLocal'])
                        ])

                        # Primero actualizamos los productos
                        if product_templates:
                            for product_template in product_templates:
                                print(f"Actualizando plantilla de producto: {product_template.name}")
                                product_template.write({
                                    'public_categ_ids': [(4, existing_category.id, False)]
                                })

                        # Luego actualizamos la categoría
                        if existing_category:
                            try:
                                existing_category.write({
                                    'image_1920': image_data,
                                    'website_description': website_description,
                                    'sequence': 10
                                })
                            except Exception as e:
                                print(f"Error al actualizar la categoría: {e}")
                                # En caso de error, intentamos mover los productos a otra categoría
                                default_category = self.env['product.public.category'].search([
                                    ('name', '=', 'Vehículos')
                                ], limit=1)
                                if default_category and product_templates:
                                    for product_template in product_templates:
                                        product_template.write({
                                            'public_categ_ids': [(4, default_category.id, False)]
                                        })

                print("*" * 80)
                return response.json()
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error al realizar la solicitud: {e}")

    # def parse_date(date_str):
    #     try:
    #         return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
    #     except ValueError:
    #         return None

    @staticmethod
    def fetch_image(url):
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            return base64.b64encode(response.content)
        except requests.exceptions.RequestException as e:
            # Handle the error (e.g., log it, return None, etc.)
            print(f"Error fetching image from {url}: {e}")
            return None
