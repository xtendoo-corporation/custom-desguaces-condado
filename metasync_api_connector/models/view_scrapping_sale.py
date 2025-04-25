from odoo import models, fields, api, tools

class ViewScrappingSale(models.Model):
    _name = 'view.scrapping.sale'
    _description = 'View Scrapping Sale'
    _auto = False

    id = fields.Integer(
        string='ID',
        readonly=True
    )
    seller_id = fields.Many2one(
        comodel_name='res.users',
        string='Seller',
        readonly=True
    )
    name = fields.Char(
        string='Code',
        readonly=True
    )
    payment_code = fields.Char(
        string='Payment Code',
        readonly=True
    )
    customer_id = fields.Char(
        string='Customer ID',
        readonly=True
    )
    tracking_url = fields.Char(
        string='Tracking URL',
        readonly=True
    )
    payment_state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('waiting_confirmation', 'Waiting Confirmation'),
            ('paid', 'Paid'),
            ('failed', 'Failed'),
            ('pending_refund', 'Pending Refund'),
            ('refunded', 'Refunded')
        ],
        string='Payment State',
        readonly=True
    )
    payment_method = fields.Selection(
        selection=[
            ('unknown', 'Unknown'),
            ('account', 'Account'),
            ('card', 'Card'),
            ('transfer', 'Transfer'),
            ('paypal', 'Paypal'),
            ('bizum', 'Bizum'),
            ('others', 'Others')
        ],
        string='Payment Method',
        readonly=True
    )
    amount_untaxed = fields.Float(
        string='Base Amount',
        digits='Product Price',
        readonly=True
    )
    discount_percentage = fields.Float(
        string='Discount %',
        readonly=True
    )
    amount_discount = fields.Float(
        string='Discount',
        readonly=True
    )
    amount_subtotal = fields.Float(
        string='Subtotal',
        readonly=True
    )
    amount_tax_percentage = fields.Float(
        string='VAT %',
        readonly=True
    )
    amount_tax = fields.Float(
        string='VAT',
        readonly=True
    )
    amount_total = fields.Float(
        string='Total',
        readonly=True
    )
    note = fields.Text(
        string='Notes',
        readonly=True
    )
    partner_invoice_id = fields.Many2one(
        comodel_name='address',
        string='Billing Address',
        readonly=True
    )
    partner_shipping_id = fields.Many2one(
        comodel_name='address',
        string='Shipping Address',
        readonly=True
    )
    partner_origin_id = fields.Many2one(
        comodel_name='address',
        string='Shipping Origin',
        readonly=True
    )
    store_pickup = fields.Boolean(
        string='Store Pickup',
        readonly=True
    )
    sale_line_ids = fields.One2many(
        comodel_name='line.scrapyard.sale',
        inverse_name='sale_id',
        string='Lines',
        readonly=True
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW %s AS (
                SELECT
                    id,
                    seller_id,
                    code as name,
                    payment_code,
                    customer_id,
                    tracking_url,
                    payment_state,
                    payment_method,
                    base_amount as amount_untaxed,
                    discount_percentage,
                    discount as amount_discount,
                    subtotal as amount_subtotal,
                    vat_percentage as amount_tax_percentage,
                    vat as amount_tax,
                    total as amount_total,
                    notes as note,
                    billing_id as partner_invoice_id,
                    shipping_id as partner_shipping_id,
                    shipping_origin_id as partner_origin_id,
                    store_pickup
                FROM scrapyard_sale
            )
        """ % self._table)
