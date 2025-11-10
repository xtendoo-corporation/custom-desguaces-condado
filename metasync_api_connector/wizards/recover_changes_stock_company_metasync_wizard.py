from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import requests
import json
from datetime import datetime


class RecoverChangesStockCompanyMetasyncWizard(models.TransientModel):
    _name = 'recover.changes.stock.company.metasync.wizard'
    _description = 'Recuperar Cambios Stock Company Metasync'

    fecha = fields.Datetime(string='Fecha', required=True, default=fields.Datetime.now)
    lastid = fields.Char(string='Last ID', required=True,
                                default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
                                    'metasync.lastid', '0'))
    offset = fields.Integer(string='Offset', required=True, default=10)

    def recuperar_cambios_almacen_empresa_metasync(self):
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

            # 2. Recuperar PIEZAS
            headers_pieces = {
                'apikey': api_key,
                'fecha': self.fecha.strftime('%d/%m/%Y %H:%M:%S'),
                'lastid': str(self.lastid),
                'offset': str(self.offset),
                'idempresa': str(idempresa)
            }

            resp_piezas = requests.get('https://apis.metasync.com/Almacen/RecuperarCambiosCanalEmpresa2',
                                       headers=headers_pieces)
            resp_piezas.raise_for_status()
            data_piezas = resp_piezas.json()

            # Imprimir la respuesta JSON completa
            print("=" * 80)
            print("RESPUESTA JSON COMPLETA DE LA API:")
            print("=" * 80)
            print(json.dumps(data_piezas, indent=2, ensure_ascii=False))
            print("=" * 80)

            # Actualizar lastid de piezas si está presente
            if 'result_set' in data_piezas and 'lastId' in data_piezas['result_set']:
                nuevo_lastid = str(data_piezas['result_set']['lastId'])

            # Procesar vehículos
            total_vehiculos = len(data_piezas.get('vehiculos', []))
            print(f"\n{'='*80}")
            print(f"PROCESAMIENTO DE VEHÍCULOS - Total recibidos: {total_vehiculos}")
            print(f"{'='*80}")

            for idx, vehiculo in enumerate(data_piezas.get('vehiculos', []), 1):
                id_local = vehiculo.get('idLocal', 'N/A')
                estados = vehiculo.get('estado', [])
                print(f"[VEHICLE {idx}/{total_vehiculos}] ID Local: {id_local} - Estados: {estados} - Tipo: {type(estados)}")

                if isinstance(estados, list) and 4 in estados:
                    vehicle_result, status = self._process_vehicle(vehiculo)
                    if vehicle_result:
                        vehicles_dict[str(vehiculo['idLocal'])] = vehicle_result
                        stats['vehicles'][status] += 1
                    else:
                        stats['vehicles']['skipped'] += 1
                else:
                    print(f"[VEHICLE {idx}/{total_vehiculos}] ⚠️ OMITIDO - No cumple filtro de estado 4")
                    stats['vehicles']['skipped'] += 1

            print(f"{'='*80}")
            print(f"VEHÍCULOS PROCESADOS: {len(vehicles_dict)} de {total_vehiculos}")
            print(f"{'='*80}\n")

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

            # Procesar piezas
            total_piezas = len(data_piezas.get('piezas', []))
            piezas_almacenadas = 0
            print(f"\n{'='*80}")
            print(f"PROCESAMIENTO DE PIEZAS - Total recibidas: {total_piezas}")
            print(f"{'='*80}")

            for idx, pieza in enumerate(data_piezas.get('piezas', []), 1):
                ubicacion = pieza.get('ubicacion', None)
                ref_local = pieza.get('refLocal', 'N/A')

                # Solo procesar piezas con ubicación "Almacenada" (valor 1)
                if ubicacion == 1:
                    piezas_almacenadas += 1
                    if piezas_almacenadas <= 5 or piezas_almacenadas == total_piezas:  # Mostrar las primeras 5 y la última
                        print(f"[PIECE {idx}/{total_piezas}] Procesando pieza almacenada: {ref_local}")
                    status = self._process_piece(pieza, situacion_map, type_material_map, vehicles_dict)
                    stats['pieces'][status] += 1
                else:
                    if idx <= 3:  # Solo mostrar las primeras 3 omitidas
                        print(f"[PIECE {idx}/{total_piezas}] ⚠️ OMITIDA - Ref: {ref_local} - Ubicación: {ubicacion} (no almacenada)")
                    stats['pieces']['skipped'] += 1

            print(f"{'='*80}")
            print(f"PIEZAS PROCESADAS: {piezas_almacenadas} almacenadas de {total_piezas} totales")
            print(f"{'='*80}\n")

            # Actualizar los lastid en el wizard actual
            self.write({
                'lastid': nuevo_lastid,
            })

            # Guardar los valores permanentemente en parámetros del sistema
            self.env['ir.config_parameter'].sudo().set_param('metasync.lastid', nuevo_lastid)

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
        id_local = vehiculo_data.get('idLocal')
        if not id_local:
            print(f"[VEHICLE] ❌ SKIPPED - Sin ID Local")
            return None, 'skipped'

        existing_vehicle = self.env['product.vehicle'].search([
            ('id_local', '=', str(id_local))
        ], limit=1)

        if existing_vehicle:
            print(f"[VEHICLE] 🔄 EXISTE - ID Local: {id_local} - Actualizando...")
        else:
            print(f"[VEHICLE] ✨ NUEVO - ID Local: {id_local} - Creando...")

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

        # Crear o actualizar
        try:
            if existing_vehicle:
                existing_vehicle.write(vehicle_vals)
                print(f"[VEHICLE] ✅ ACTUALIZADO - ID Local: {id_local} - Nombre: {vehicle_name}")
                return existing_vehicle, 'updated'
            else:
                new_vehicle = self.env['product.vehicle'].create(vehicle_vals)
                print(f"[VEHICLE] ✅ CREADO - ID Local: {id_local} - Nombre: {vehicle_name}")
                return new_vehicle, 'created'
        except Exception as e:
            print(f"[VEHICLE] ❌ ERROR - ID Local: {id_local} - Error: {str(e)}")
            return None, 'error'

    def _process_piece(self, pieza, situacion_map, type_material_map, vehicles_dict):
        """Procesa una pieza y devuelve el estado de la operación"""
        ref_local = ''
        try:
            # Validar datos mínimos
            ref_local = pieza.get('refLocal', '')
            descripcion = pieza.get('descripcionArticulo', '')

            if not ref_local or not descripcion:
                print(f"[PIECE] ❌ SKIPPED - Sin ref_local o descripción - Ref: {ref_local}")
                return 'skipped'

            print(f"[PIECE] 🔍 PROCESANDO - Ref: {ref_local} - {descripcion[:50]}...")

            # Obtener imagen
            image_data = None
            product_image_vals = []

            if pieza.get('urlsImgs'):
                first_image_url = pieza['urlsImgs'][0] + ".jpeg"
                image_data = self.fetch_image(first_image_url)

                for i, url in enumerate(pieza.get('urlsImgs', [])):
                    img_url = url + ".jpeg"
                    img_data = self.fetch_image(img_url)
                    if img_data:
                        product_image_vals.append((0, 0, {
                            'name': f"{ref_local}_{i + 1}",
                            'image_1920': img_data,
                            'sequence': i + 1,
                        }))

            # Mapear ubicación y tipo de material
            ubicacion = pieza.get('ubicacion', 9)
            ubicacion_texto = situacion_map.get(ubicacion, "Situación Desconocida")

            tipo_material = pieza.get('tipoMaterial', 3)
            tipo_material_texto = type_material_map.get(tipo_material, "Tipo Desconocido")

            # Formatear fecha
            date_str = pieza.get('fechaMod', '')
            formatted_date = ''
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                    formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass

            # Buscar vehículo relacionado
            vehicle_id = None
            id_vehiculo = str(pieza.get('idVehiculo', ''))
            if id_vehiculo and id_vehiculo != '0':
                vehicle = vehicles_dict.get(id_vehiculo)
                if vehicle:
                    vehicle_id = vehicle.id
                    print(f"[PIECE] 🚗 RELACIÓN - Ref: {ref_local} vinculada al vehículo ID Local: {id_vehiculo}")
                else:
                    print(f"[PIECE] ⚠️ ADVERTENCIA - Ref: {ref_local} - Vehículo ID Local: {id_vehiculo} no encontrado")

            # Buscar o crear categoría
            category = self._get_or_create_category(pieza)

            # Buscar producto existente
            product = self.env['product.template'].search([
                ('default_code', '=', ref_local)
            ], limit=1)

            if product:
                print(f"[PIECE] 🔄 EXISTE - Ref: {ref_local} - Actualizando...")
            else:
                print(f"[PIECE] ✨ NUEVO - Ref: {ref_local} - Creando...")

            # Preparar valores
            vals = {
                'name': descripcion,
                'default_code': ref_local,
                'categ_id': category.id,
                'list_price': (pieza.get('precio', 0) or 0) / 100,
                'weight': pieza.get('peso', 0),
                'image_1920': image_data,
                'product_image_ids': product_image_vals,  # Todas las imágenes para la galería
                'principal_ref': pieza.get('refPrincipal', ''),
                'version_code': pieza.get('codVersion', ''),
                'article_code': pieza.get('codArticulo', ''),
                'stock_year': pieza.get('anyoStock', ''),
                'location': ubicacion_texto,
                'observations': pieza.get('observaciones', ''),
                'reserve': pieza.get('reserva', ''),
                'material_type': tipo_material_texto,
                'modification_date': formatted_date,
                'cod_almacen': pieza.get('codAlmacen', ''),
                'website_published': True,
                'vehicle_id': id_vehiculo,  # Relación con el vehículo
                'product_vehicle_id': vehicle_id,
            }

            if product:
                product.product_image_ids.unlink()
                product.write(vals)
                print(f"[PIECE] ✅ ACTUALIZADA - Ref: {ref_local} - {descripcion[:50]}")
                return 'updated'
            else:
                # Crear categorías públicas
                public_categ_ids = self._get_or_create_public_categories(pieza)
                vals['public_categ_ids'] = [(6, 0, public_categ_ids)]
                self.env['product.template'].create(vals)
                print(f"[PIECE] ✅ CREADA - Ref: {ref_local} - {descripcion[:50]}")
                return 'created'

        except Exception as e:
            print(f"[PIECE] ❌ ERROR - Ref: {ref_local} - Error: {str(e)}")
            return 'error'

    def _get_or_create_category(self, pieza):
        """Obtiene o crea la categoría de producto"""
        cod_familia = pieza.get('codFamilia', '')
        desc_familia = pieza.get('descripcionFamilia', '')

        if not cod_familia or not desc_familia:
            return self.env.ref('product.product_category_all')

        category = self.env['product.category'].search([
            ('default_code', '=', cod_familia)
        ], limit=1)

        if not category:
            category = self.env['product.category'].create({
                'name': desc_familia,
                'default_code': cod_familia,
                'parent_id': self.env.ref('product.product_category_1').id,
            })

        return category

    def _get_or_create_public_categories(self, pieza):
        """Obtiene o crea categorías públicas"""
        # Categoría padre "Vehículos"
        vehiculos_categ = self.env['product.public.category'].search([
            ('name', '=', 'Vehículos')
        ], limit=1)

        if not vehiculos_categ:
            vehiculos_categ = self.env['product.public.category'].create({
                'name': 'Vehículos',
                'sequence': 1
            })

        # Categoría específica
        desc_familia = pieza.get('descripcionFamilia', '')
        if not desc_familia:
            return [vehiculos_categ.id]

        familia_categ = self.env['product.public.category'].search([
            ('name', '=', desc_familia)
        ], limit=1)

        if not familia_categ:
            familia_categ = self.env['product.public.category'].create({
                'name': desc_familia,
                'parent_id': vehiculos_categ.id,
                'sequence': 10
            })

        return [vehiculos_categ.id, familia_categ.id]

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
            return None
