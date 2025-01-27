from odoo import models, api
import base64
import requests
from odoo.exceptions import UserError
from datetime import datetime


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def obtener_parametros_con_empresa_metasync(self):
        config = self.env['ir.config_parameter'].sudo()
        api_key = config.get_param('metasync.inventory.apikey', default=None)
        idempresa = config.get_param('metasync.id_empresa', default=None)
        if not api_key or not idempresa:
            raise UserError(
                "Por favor, configure los parámetros 'metasync.inventory.apikey' y 'metasync.id_empresa' en Ajustes > Parámetros > Parámetros del sistema.")
        return api_key, idempresa

    def obtener_parametros_metasync(self):
        config = self.env['ir.config_parameter'].sudo()
        api_key = config.get_param('metasync.inventory.apikey', default=None)
        if not api_key:
            raise UserError(
                "Por favor, configure los parámetros 'metasync.inventory.apikey'  en Ajustes > Parámetros > Parámetros del sistema.")
        return api_key

    @api.model
    def recuperar_cambios_almacen_metasync(self):
        print("*" * 80)
        api_key = self.obtener_parametros_metasync()
        fecha = '20/12/2023 21:29:56'
        lastid = "0"
        offset = "1000"
        headers = {
            'apiKey': api_key,
            'fecha': fecha,
            'lastid': lastid,
            'offset': offset,
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
            response = requests.get('https://apis.metasync.com/Almacen/RecuperarCambiosCanal', headers=headers)
            response.raise_for_status()  # Lanza un error si la respuesta no es 200
            # Acceder a las piezas
            if len(response.json()['piezas']) == 0:
                print("No hay piezas")
            else:
                for pieza in response.json()['piezas']:
                    print('---')
                    print(f"ID Empresa: {pieza['idEmpresa']}")
                    print(f"Referencia local: {pieza['refLocal']}")
                    print(f"ID Vehículo: {pieza['idVehiculo']}")
                    print(f"Código Familia: {pieza['codFamilia']}")
                    print(f"Descripción Familia: {pieza['descripcionFamilia']}")
                    print(f"Código Artículo: {pieza['codArticulo']}")
                    print(f"Descripción del artículo: {pieza['descripcionArticulo']}")
                    print(f"Código Versión: {pieza['codVersion']}")
                    print(f"Referencia Principal: {pieza['refPrincipal']}")
                    print(f"Precio: {pieza['precio']}")
                    print(f"Año Stock: {pieza['anyoStock']}")
                    print(f"Peso: {pieza['peso']}")
                    ubicacion_texto = situacion_map.get(pieza['ubicacion'], "Situación Desconocida")
                    print(f"Ubicación: {ubicacion_texto}")
                    print(f"Observaciones: {pieza['observaciones']}")
                    print(f"Reserva: {pieza['reserva']}")
                    tipo_material_texto = type_material_map.get(pieza['tipoMaterial'], "Tipo Desconocido")
                    print(f"Tipo Material: {tipo_material_texto}")
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
                    is_product = self.env['product.product'].search([('default_code', '=', pieza['refLocal'])])
                    if is_product:
                        print(f"El producto {pieza['descripcionArticulo']} ya existe en la base de datos")
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
                        # image_url = pieza['urlsImgs'][0] + ".jpeg"
                        # image_response = requests.get(image_url)
                        # if image_response.status_code == 200:
                        #     image_data = base64.b64encode(image_response.content)
                        # else:
                        #     image_data = False
                        print(f"Creando el producto {pieza['descripcionArticulo']}:")
                        product = self.env['product.product'].create({
                            'name': pieza['descripcionArticulo'],
                            'default_code': pieza['refLocal'],
                            'categ_id': category.id,
                            'list_price': pieza['precio'] / 1000,
                            'weight': pieza['peso'],
                            # 'image_1920': image_data,
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
                        })
            # Acceder a los vehículos
            if len(response.json()['vehiculos']) == 0:
                print("No hay vehículos")
            else:
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
            print("*" * 80)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error al realizar la solicitud: {e}")

    @api.model
    def recuperar_cambios_almacen_empresa_metasync(self):
        print("*" * 80)
        api_key, idempresa = self.obtener_parametros_con_empresa_metasync()
        fecha = '20/12/2023 21:29:56'
        lastid = "0"
        offset = "1000"
        headers = {
            'apiKey': api_key,
            'fecha': fecha,
            'lastid': lastid,
            'offset': offset,
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
                    print(f"ID Empresa: {pieza['idEmpresa']}")
                    print(f"Referencia local: {pieza['refLocal']}")
                    print(f"ID Vehículo: {pieza['idVehiculo']}")
                    print(f"Código Familia: {pieza['codFamilia']}")
                    print(f"Descripción Familia: {pieza['descripcionFamilia']}")
                    print(f"Código Artículo: {pieza['codArticulo']}")
                    print(f"Descripción del artículo: {pieza['descripcionArticulo']}")
                    print(f"Código Versión: {pieza['codVersion']}")
                    print(f"Referencia Principal: {pieza['refPrincipal']}")
                    print(f"Precio: {pieza['precio']}")
                    print(f"Año Stock: {pieza['anyoStock']}")
                    print(f"Peso: {pieza['peso']}")
                    ubicacion_texto = situacion_map.get(pieza['ubicacion'], "Situación Desconocida")
                    print(f"Ubicación: {ubicacion_texto}")
                    print(f"Observaciones: {pieza['observaciones']}")
                    print(f"Reserva: {pieza['reserva']}")
                    tipo_material_texto = type_material_map.get(pieza['tipoMaterial'], "Tipo Desconocido")
                    print(f"Tipo Material: {tipo_material_texto}")
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
                    is_product = self.env['product.product'].search([('default_code', '=', pieza['refLocal'])])
                    if is_product:
                        print(f"El producto {pieza['descripcionArticulo']} ya existe en la base de datos")
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
                        # image_url = pieza['urlsImgs'][0] + ".jpeg"
                        # image_response = requests.get(image_url)
                        # if image_response.status_code == 200:
                        #     image_data = base64.b64encode(image_response.content)
                        # else:
                        #     image_data = False
                        print(f"Creando el producto {pieza['descripcionArticulo']}:")
                        product = self.env['product.product'].create({
                            'name': pieza['descripcionArticulo'],
                            'default_code': pieza['refLocal'],
                            'categ_id': category.id,
                            'list_price': pieza['precio'] / 100,
                            'weight': pieza['peso'],
                            # 'image_1920': image_data,
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
                        })
                    # Acceder a los vehículos
                if len(response.json()['vehiculos']) == 0:
                    print("No hay vehículos")
                else:
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
                print("*" * 80)
                return response.json()
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error al realizar la solicitud: {e}")


    @api.model
    def recuperar_cambios_vehiculos_metasync(self):
        print("*" * 80)
        api_key = self.obtener_parametros_metasync()
        fecha = '20/12/2023 21:29:56'
        lastid = "0"
        offset = "50"

        headers = {
            'apiKey': api_key,
            'fecha': fecha,
            'lastid': lastid,
            'offset': offset,
        }

        try:
            response = requests.get('https://apis.metasync.com/Almacen/RecuperarCambiosVehiculosCanal',
                                    headers=headers)
            response.raise_for_status()  # Lanza un error si la respuesta no es 200
            # Acceder a las piezas
            print("/" * 80)
            if len(response.json()['vehiculos']) == 0:
                print("No hay vehículos")
            else:
                for vehiculo in response.json()['vehiculos']:
                    print(f"ID del vehículo: {vehiculo['idLocal']}")
                    print(f"Marca del vehículo: {vehiculo['nombreMarca']}")
                    print(f"Modelo del vehículo: {vehiculo['nombreModelo']}")
                    print('---')
            print("/" * 80)
            return response.json()

        except requests.exceptions.RequestException as e:
            raise UserError(f"Error al realizar la solicitud: {e}")


    @api.model
    def recuperar_cambios_vehiculos_empresa_metasync(self):
        print("*" * 80)
        api_key, idempresa = self.obtener_parametros_con_empresa_metasync()
        fecha = '20/12/2023 21:29:56'
        lastid = "0"
        offset = "50"

        headers = {
            'apiKey': api_key,
            'fecha': fecha,
            'lastid': lastid,
            'offset': offset,
            'idempresa': idempresa
        }

        try:
            response = requests.get('https://apis.metasync.com/Almacen/RecuperarCambiosVehiculosEmpresa', headers=headers)
            response.raise_for_status()  # Lanza un error si la respuesta no es 200
            # Acceder a las piezas
            print("/" * 80)
            if len(response.json()['vehiculos']) == 0:
                print("No hay vehículos")
            else:
                for vehiculo in response.json()['vehiculos']:
                    print(f"ID del vehículo: {vehiculo['idLocal']}")
                    print(f"Marca del vehículo: {vehiculo['nombreMarca']}")
                    print(f"Modelo del vehículo: {vehiculo['nombreModelo']}")
                    print('---')
            print("/" * 80)
            return response.json()

        except requests.exceptions.RequestException as e:
            raise UserError(f"Error al realizar la solicitud: {e}")
