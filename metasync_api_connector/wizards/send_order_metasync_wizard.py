from odoo import models, fields, api
from odoo.exceptions import UserError
import json
import requests


class SendOrderMetasyncWizard(models.TransientModel):
    _name = 'send.order.metasync.wizard'
    _description = 'Wizard para enviar pedidos a MetaSync'

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Pedido',
        required=True
    )

    def action_send_order(self):
        self.ensure_one()
        api_key = self.env['ir.config_parameter'].sudo().get_param('metasync.inventory.apikey')
        idempresa = self.env['ir.config_parameter'].sudo().get_param('metasync.id_empresa')

        if not api_key or not idempresa:
            raise UserError("Faltan credenciales de MetaSync")

        self.env.context = dict(self.env.context)
        self.order_id.action_synchronize_order()
        order_data = json.loads(self.env.context.get('sale_order_json'))

        print("\n=== JSON DEL PEDIDO ===")
        print(json.dumps(order_data, indent=2, ensure_ascii=False))
        print("=====================\n")

        headers = {
            "apikey": api_key,
            "idempresa": str(idempresa),
            "accept": "application/json",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                'https://api.metasync.com/Pedidos/CrearPedido',
                headers=headers,
                json=order_data
            )
            if response.status_code == 200:
                self.order_id.is_synchronized = True
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Pedido sincronizado correctamente',
                        'type': 'success',
                    }
                }
            elif response.status_code == 400:
                raise UserError(f"Error al insertar el pedido: {response.text}")
            elif response.status_code == 500:
                raise UserError(f"Error interno del servidor MetaSync: {response.text}")
            else:
                raise UserError(f"Error desconocido (código {response.status_code}): {response.text}")

        # except requests.exceptions.ConnectionError:
        #     raise UserError("Error de conexión: No se pudo conectar al servidor de MetaSync")
        except requests.exceptions.Timeout:
            raise UserError("Error de conexión: El servidor tardó demasiado en responder")
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error en la petición: {str(e)}")
