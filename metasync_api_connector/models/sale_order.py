from odoo import models, fields, api
import json


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_synchronized = fields.Boolean(
        string='Syncronized',
        default=False,
        readonly=True,
    )

    def _get_payment_status_map(self):
        return {
            'draft': 0,  # Pendiente
            'sent': 1,  # EsperaConfirmacion
            'sale': 2,  # Pagado
            'done': 2,  # Pagado
            'cancel': 3,  # Fallido
        }

    def _get_order_status_map(self):
        return {
            'draft': 0,  # Desconocido
            'sent': 1,  # EnSeguimiento
            'sale': 2,  # Reservado
            'done': 5,  # Entregado
            'cancel': 6,  # Anulado
        }

    def _get_payment_method_map(self):
        return {
            'transfer': 3,  # Transferencia
            'electronic': 2,  # Tarjeta
            'paypal': 4,  # PayPal
            'other': 6,  # Otros
        }

    def _prepare_order_header(self):
        payment_method = (
            self.payment_acquirer_id.provider
            if hasattr(self, 'payment_acquirer_id')
            else 'other'
        )
        return {
            "Iva": self.amount_tax,
            "Base": self.amount_untaxed,
            "Total": self.amount_total,
            "Codigo": self.name,
            "Subtotal": self.amount_untaxed,
            "Descuento": 0,
            "FormaPago": self._get_payment_method_map().get(payment_method, 6),
            "IdCliente": self.partner_id.email,
            "CodigoPago": self.name,
            "EstadoPago": self._get_payment_status_map().get(self.state, 0),
            "IdVendedor": 1476,
            "Observaciones": self.name,
            "PorcentajeIva": 21,
            "RecogidaTienda": False,
            "SeguimientoUrl": None,
            "PorcentajeDescuento": 0
        }

    def _prepare_customer_data(self, partner):
        return {
            "Pais": partner.country_id.name,
            "Tipo": 0,
            "Email": partner.email,
            "NifCif": partner.vat or "",
            "Domicilio": partner.street or "",
            "Poblacion": partner.city or "",
            "Provincia": partner.state_id.name or "",
            "Telefono1": partner.phone,
            "Telefono2": partner.mobile or "",
            "RazonSocial": partner.name or "",
            "CodigoPostal": partner.zip or "",
            "Observaciones": "",
            "NombreComercial": partner.name or "",
        }

    def _prepare_shipping_data(self):
        shipping_data = self._prepare_customer_data(self.partner_shipping_id)
        shipping_data.update({
            "Tipo": 1,
            "Descripcion": "Facturacion"
        })
        return shipping_data

    def _prepare_line_data(self, line):
        return {
            "Base": float(line.price_subtotal),
            "Tipo": 1 if line.product_id.type != 'service' else 2,
            "Precio": float(line.price_unit),
            "Cantidad": int(line.product_uom_qty),
            "Concepto": line.name,
            "Subtotal": float(line.price_subtotal),
            "Descuento": float(line.discount),
            "Referencia": line.product_id.default_code,
            "PorcentajeDescuento": float(line.discount)
        }

    def _prepare_order_lines(self):
        return [self._prepare_line_data(line) for line in self.order_line]

    def action_synchronize_order(self):
        self.ensure_one()
        order_data = {
            "Pedido": self._prepare_order_header(),
            "Cliente": self._prepare_customer_data(self.partner_id),
            "Envio": self._prepare_shipping_data(),
            "Lineas": self._prepare_order_lines()
        }

        self.env.context = dict(self.env.context)
        self.env.context['sale_order_json'] = json.dumps(order_data)
        self.is_synchronized = True

        return {
            'name': 'Enviar a MetaSync',
            'type': 'ir.actions.act_window',
            'res_model': 'send.order.metasync.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
            }
        }
