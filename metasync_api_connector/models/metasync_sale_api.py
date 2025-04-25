from odoo import models, fields, api
from odoo.exceptions import UserError
import requests

class MetasyncSaleAPI(models.Model):
    _name = 'metasync.order.api'
    _description = 'Metasync Order API Connector'

    def _get_api_credentials(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param('metasync.order.apikey')
        company_id = self.env['ir.config_parameter'].sudo().get_param('metasync.company_id')

        if not api_key or not company_id:
            raise UserError("Metasync API credentials are not configured")

        return api_key, company_id

    def create_order(self, order_data):
        """Create a new order in Metasync"""
        api_key, company_id = self._get_api_credentials()

        headers = {
            'apiKey': api_key,
            'idempresa': str(company_id),
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(
                'https://apis.metasync.com/Pedidos/CrearPedido',
                headers=headers,
                json=order_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error creating order: {str(e)}")

    def update_status(self, code, status):
        """Update order status"""
        api_key, company_id = self._get_api_credentials()

        headers = {
            'apiKey': api_key,
            'idempresa': str(company_id),
            'codigo': code,
            'estado': str(status)
        }

        try:
            response = requests.post(
                'https://apis.metasync.com/Pedidos/ActualizarEstado',
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error updating status: {str(e)}")

    def add_tracking(self, code, tracking_url):
        """Add tracking URL to order"""
        api_key, company_id = self._get_api_credentials()

        headers = {
            'apiKey': api_key,
            'idempresa': str(company_id),
            'codigo': code,
            'url': tracking_url
        }

        try:
            response = requests.post(
                'https://apis.metasync.com/Pedidos/AgregarSeguimiento',
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error adding tracking: {str(e)}")

    def cancel_order(self, code):
        """Cancel existing order"""
        api_key, company_id = self._get_api_credentials()

        headers = {
            'apiKey': api_key,
            'idempresa': str(company_id),
            'codigo': code
        }

        try:
            response = requests.post(
                'https://apis.metasync.com/Pedidos/AnularPedido',
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error canceling order: {str(e)}")

    def get_original_order(self, code):
        """Get complete order information"""
        api_key, company_id = self._get_api_credentials()

        headers = {
            'apiKey': api_key,
            'idempresa': str(company_id),
            'codigo': code
        }

        try:
            response = requests.get(
                'https://apis.metasync.com/Pedidos/RecuperarPedidoOrigen',
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error retrieving order: {str(e)}")

    def get_tracking(self, code):
        """Get order tracking information"""
        api_key, company_id = self._get_api_credentials()

        headers = {
            'apiKey': api_key,
            'idempresa': str(company_id),
            'codigo': code
        }

        try:
            response = requests.get(
                'https://apis.metasync.com/Pedidos/ObtenerSeguimiento',
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error getting tracking: {str(e)}")
