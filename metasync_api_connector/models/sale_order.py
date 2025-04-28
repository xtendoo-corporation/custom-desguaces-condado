from odoo import models, fields, api
import json


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_synchronized = fields.Boolean(
        string='Syncronized',
        default=False,
        readonly=True,
    )

    def action_synchronize_order(self):
        self.ensure_one()
        # Mapeo de estados de pago
        estado_pago_map = {
            'draft': 0,  # Pendiente
            'sent': 1,  # EsperaConfirmacion
            'sale': 2,  # Pagado
            'done': 2,  # Pagado
            'cancel': 3,  # Fallido
        }

        # Mapeo de estados del pedido
        estado_pedido_map = {
            'draft': 0,  # Desconocido
            'sent': 1,  # EnSeguimiento
            'sale': 2,  # Reservado
            'done': 5,  # Entregado
            'cancel': 6,  # Anulado
        }

        # Mapeo de forma de pago
        forma_pago_map = {
            'transfer': 3,  # Transferencia
            'electronic': 2,  # Tarjeta
            'paypal': 4,  # PayPal
            'other': 6,  # Otros
        }

        order_data = {
            "id": 0,
            "idVendedor": self.user_id.id,
            "idCliente": self.partner_id.email,
            "codigo": self.name,
            "codigoCrvnet": "",
            "proveedor": self.company_id.name,
            "canal": "Odoo",
            "codigoPago": self.name,
            "estadoPago": estado_pago_map.get(self.state, 0),
            "formaPago": forma_pago_map.get(
                self.payment_acquirer_id.provider if hasattr(self, 'payment_acquirer_id') else 'other', 6),
            "seguimientoUrl": None,
            "base": float(self.amount_untaxed),
            "porcentajeDescuento": 0,
            "descuento": 0,
            "subtotal": float(self.amount_untaxed),
            "porcentajeIva": 21.0,
            "iva": float(self.amount_tax),
            "total": float(self.amount_total),
            "contabilizado": False,
            "lineas": self._prepare_order_lines(),
            "observaciones": self.note or self.name,
            "informacion": "",
            "idFacturacion": 0,
            "facturacion": self._prepare_partner_data(self.partner_id),
            "idOrigenEnvio": 0,
            "origenEnvio": self._prepare_partner_data(self.company_id.partner_id),
            "idEnvio": 0,
            "envio": self._prepare_partner_data(self.partner_shipping_id),
            "recogidaTienda": False,
            "documentos": [],
            "incidencias": [],
            "estado": estado_pedido_map.get(self.state, 0),  # Reservado
            "estadoAccion": estado_pago_map.get(self.state, 0),  # Procesando
            "estadoCRVNet": "",
            "fechaMod": self.write_date.isoformat(),
            "fechaIn": self.create_date.isoformat(),
            "incidenciasTotal": 0,
            "incidenciasAbiertas": 0,
            "documentosTotal": 0
        }

        print("\n=== JSON DEL PEDIDO ===")
        print(json.dumps(order_data, indent=2, ensure_ascii=False))
        print("=====================\n")

        self.env.context = dict(self.env.context)
        self.env.context['sale_order_json'] = json.dumps(order_data)

        self.is_synchronized = True
        return True

    def _prepare_partner_data(self, partner):
        return {
            "Fax": "",
            "Pais": partner.country_id.name or "ESPAÑA",
            "Tipo": 0,
            "Email": partner.email or "",
            "NifCif": partner.vat or "",
            "Domicilio": partner.street or "",
            "Poblacion": partner.city or "",
            "Provincia": partner.state_id.name or "",
            "Telefono1": partner.phone or "",
            "Telefono2": partner.mobile or "",
            "CodigoPais": partner.country_id.id,
            "Descripcion": "",
            "RazonSocial": partner.name,
            "CodigoPostal": partner.zip or "",
            "Observaciones": "",
            "CodigoPoblacion": None,
            "CodigoProvincia": partner.state_id.id,
            "NombreComercial": partner.name
        }

    def _prepare_order_lines(self):
        lines = []
        for line in self.order_line:
            line_data = {
                "Base": line.price_subtotal,
                "Tipo": 1 if line.product_id.type != 'service' else 2,
                "Precio": line.price_unit,
                "Cantidad": line.product_uom_qty,
                "Concepto": line.name,
                "Subtotal": line.price_subtotal,
                "Descuento": line.discount,
                "Referencia": line.product_id.default_code or "0000",
                "PorcentajeDescuento": line.discount
            }
            lines.append(line_data)
        return lines
