from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import requests
from datetime import datetime


class RecoverChangesStockMetasyncWizard(models.TransientModel):
    _name = 'recover.changes.stock.metasync.wizard'
    _description = 'Recuperar Cambios Stock Metasync'

    fecha = fields.Datetime(string='Fecha', required=True, default=fields.Datetime.now)
    lastid = fields.Char(string='Last ID', required=True,
                         default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
                             'metasync.lastid_vehicles', '0'))
    offset = fields.Integer(string='Offset', required=True, default=10)

    def recuperar_cambios_almacen(self):
        print("Iniciando recuperación de cambios en el almacén de la empresa Metasync... Wizard")
        self.ensure_one()

        api_key = self.env['ir.config_parameter'].sudo().get_param('metasync.inventory.apikey', default=None)
        if not api_key:
            raise UserError("No está bien configurado el parámetro 'metasync.inventory.apikey' o no es correcto.")

        idempresa = self.env['ir.config_parameter'].sudo().get_param('metasync.id_empresa', default=None)
        if not idempresa:
            raise UserError("No está bien configurado el parámetro 'metasync.id_empresa' o no es correcto.")

        stats = {
            'vehicles': {'created': 0, 'updated': 0, 'skipped': 0, 'error': 0},
            'pieces': {'created': 0, 'updated': 0, 'skipped': 0, 'error': 0}
        }

        vehicles_dict = {}
        nuevo_lastid = self.lastid

        try:
            headers_pieces = {
                'apikey': api_key,
                'fecha': self.fecha.strftime('%d/%m/%Y %H:%M:%S'),
                'lastid': str(self.lastid),
                'offset': str(self.offset),
                'idempresa': str(idempresa)
            }

            resp_vehicles = requests.get('https://apis.metasync.com/Almacen/RecuperarCambiosVehiculosCanal',
                                         headers=headers_pieces)
            resp_vehicles.raise_for_status()
            data_vehicles = resp_vehicles.json()

            if 'result_set' in data_vehicles and 'lastId' in data_vehicles['result_set']:
                nuevo_lastid = str(data_vehicles['result_set']['lastId'])
                print(f"Nuevo lastid para vehiculos: {nuevo_lastid}")

            for vehiculo in data_vehicles.get('vehiculos', []):
                estados = vehiculo.get('estado', [])
                if isinstance(estados, list) and 4 in estados:
                    print("Datos brutos del vehículo recibido:")
                    for k, v in vehiculo.items():
                        print(f"  {k}: {v}")
                    vehicle_result, status = self._process_vehicle(vehiculo)
                    if vehicle_result:
                        vehicles_dict[str(vehiculo['idLocal'])] = vehicle_result
                        stats['vehicles'][status] += 1
                    else:
                        stats['vehicles']['skipped'] += 1
                else:
                    print(f"Vehículo {vehiculo.get('idLocal')} omitido por estado: {estados}")

            self.write({
                'lastid': nuevo_lastid,
            })

            # Guardar los valores permanentemente en parámetros del sistema
            self.env['ir.config_parameter'].sudo().set_param('metasync.lastid_vehicles', nuevo_lastid)

            # 3. Mostrar resultados
            message = self._generate_results_message(stats)
            message += f"\nÚltimo ID: {nuevo_lastid}"

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Proceso Completado',
                    'message': message,
                    'type': 'success',
                    'sticky': True
                }
            }
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error al realizar la solicitud: {e}")
        except Exception as e:
            raise UserError(f"Error inesperado: {e}")

    def _process_vehicle(self, vehiculo_data):
        """Procesa un vehículo y devuelve el registro y el estado"""
        print("Procesa un vehículo y devuelve el registro y el estado Wizard:")
        id_local = vehiculo_data.get('idLocal')
        if not id_local:
            print("Vehículo sin ID local, saltando...")
            return None, 'skipped'

        existing_vehicle = self.env['product.vehicle'].search([
            ('id_local', '=', str(id_local))
        ], limit=1)

        # Helpers seguros
        def safe_int(val):
            try:
                return int(val) if val not in (None, '', False) else 0
            except (ValueError, TypeError):
                return 0

        def safe_float(val):
            try:
                return float(val) if val not in (None, '', False) else 0.0
            except (ValueError, TypeError):
                return 0.0

        # Construir nombre
        nombre_marca = vehiculo_data.get('nombreMarca', '')
        nombre_modelo = vehiculo_data.get('nombreModelo', '')
        nombre_version = vehiculo_data.get('nombreVersion', '')
        vehicle_name = f"{nombre_marca} {nombre_modelo} {nombre_version}".strip()
        if not vehicle_name:
            vehicle_name = f"Vehículo {id_local}"

        # Valores básicos
        vehicle_vals = {
            'name': vehicle_name,
            'id_local': str(id_local),
            'id_empresa': str(vehiculo_data.get('idEmpresa', '')),
            'codigo': vehiculo_data.get('codigo', ''),
            'estado': vehiculo_data.get('estado', ''),
            'bastidor': vehiculo_data.get('bastidor', ''),
            'matricula': vehiculo_data.get('matricula', ''),
            'color': vehiculo_data.get('color', ''),
            'kilometraje': safe_int(vehiculo_data.get('kilometraje')),
            'anyo_vehiculo': safe_int(vehiculo_data.get('anyoVehiculo')),
            'codigo_motor': vehiculo_data.get('codigoMotor', ''),
            'codigo_cambio': vehiculo_data.get('codigoCambio', ''),
            'observaciones': vehiculo_data.get('observaciones', ''),
            'cod_marca': vehiculo_data.get('codMarca', ''),
            'nombre_marca': nombre_marca,
            'cod_modelo': vehiculo_data.get('codModelo', ''),
            'nombre_modelo': nombre_modelo,
            'cod_version': vehiculo_data.get('codVersion', ''),
            'nombre_version': nombre_version,
            'tipo_version': vehiculo_data.get('tipoVersion', ''),
            'combustible': vehiculo_data.get('combustible', ''),
            'puertas': safe_int(vehiculo_data.get('puertas')),
            'anyo_inicio': safe_int(vehiculo_data.get('anyoInicio')),
            'anyo_fin': safe_int(vehiculo_data.get('anyoFin')),
            'tipos_motor': vehiculo_data.get('tiposMotor', ''),
            'potencia_hp': safe_float(vehiculo_data.get('potenciaHP')),
            'potencia_kw': safe_float(vehiculo_data.get('potenciaKw')),
            'cilindrada': safe_int(vehiculo_data.get('cilindrada')),
            'transmision': vehiculo_data.get('transmision', ''),
            'alimentacion': vehiculo_data.get('alimentacion', ''),
            'num_marchas': safe_int(vehiculo_data.get('numMarchas')),
            'rv_code': vehiculo_data.get('rvCode', ''),
            'ktype': vehiculo_data.get('ktype', ''),
            'website_published': True,
        }

        # Manejar fecha de modificación
        fecha_str = vehiculo_data.get('fechaMod')
        if fecha_str:
            for fmt in ('%Y-%m-%dT%H:%M:%S', '%d/%m/%Y %H:%M:%S'):
                try:
                    vehicle_vals['fecha_mod'] = datetime.strptime(fecha_str, fmt)
                    break
                except Exception:
                    continue
            else:
                print(f"Error convirtiendo fechaMod: {fecha_str}")

        # Procesar imágenes
        urls_imgs = vehiculo_data.get('urlsImgs', [])
        if existing_vehicle:
            # Si actualizamos, primero limpiamos las antiguas
            existing_vehicle.image_ids.unlink()
        if urls_imgs:
            image_vals = [
                (0, 0, {
                    'url': url,
                    'sequence': i
                }) for i, url in enumerate(urls_imgs, start=1)
            ]
            vehicle_vals['image_ids'] = image_vals

        vehicle_vals['urls_imgs'] = '\n'.join(urls_imgs) if urls_imgs else ''

        # Debug
        print("Datos del vehículo a procesar:")
        for key, value in vehicle_vals.items():
            print(f"  {key}: {value}")

        # Crear o actualizar
        try:
            if existing_vehicle:
                print(f"Actualizando vehículo ID {id_local}")
                existing_vehicle.write(vehicle_vals)
                return existing_vehicle, 'updated'
            else:
                print(f"Creando nuevo vehículo ID {id_local}")
                new_vehicle = self.env['product.vehicle'].create(vehicle_vals)
                return new_vehicle, 'created'
        except Exception as e:
            print(f"Error procesando vehículo {id_local}: {str(e)}")
            return None, 'error'


    def _generate_results_message(self, stats):
        """Genera el mensaje de resultados con estadísticas"""
        # Estadísticas de vehículos
        v_created = stats['vehicles']['created']
        v_updated = stats['vehicles']['updated']
        v_skipped = stats['vehicles']['skipped']
        v_error = stats['vehicles']['error']
        v_total = v_created + v_updated + v_skipped + v_error

        # Estadísticas de piezas
        p_created = stats['pieces']['created']
        p_updated = stats['pieces']['updated']
        p_skipped = stats['pieces']['skipped']
        p_error = stats['pieces']['error']
        p_total = p_created + p_updated + p_skipped + p_error

        # Construir mensaje
        message = f"""
           Resumen del Procesamiento:

              (1) Vehículos: Total procesados: {v_total}, creados: {v_created}, actualizados: {v_updated}, omitidos: {v_skipped} y errores: {v_error};
              (2) Piezas: Total procesadas: {p_total}, creadas: {p_created}, actualizadas: {p_updated}, omitidas: {p_skipped} y errores: {p_error};
              (3) Relaciones: Piezas relacionadas con vehículos: {p_created + p_updated - p_skipped}.
           """

        return message


    @staticmethod
    def fetch_image(url):
        """Obtiene imagen desde URL"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return base64.b64encode(response.content)
        except requests.exceptions.RequestException as e:
            print(f"Error obteniendo imagen: {e}")
            return None
