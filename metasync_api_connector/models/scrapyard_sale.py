from odoo import models, fields, api

class ScrapyardSale(models.Model):
    _name = 'scrapyard.sale'
    _description = 'Scrapyard Sale'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]
    _order = 'id desc'

    name = fields.Char(
        string='Code',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )
    seller_id = fields.Many2one(
        comodel_name='res.users',
        string='Seller',
        required=True
    )
    supplier = fields.Char(string='Supplier')
    channel = fields.Char(string='Channel')
    customer_id = fields.Char(string='Customer ID')
    payment_code = fields.Char(string='Payment Code')
    crvnet_code = fields.Char(string='CRVNet Code')
    tracking_url = fields.Char(string='Tracking URL')
    state = fields.Selection(
        selection=[
            ('unknown', 'Unknown'),
            ('tracking', 'Tracking'),
            ('reserved', 'Reserved'),
            ('processing', 'Processing'),
            ('shipping', 'Shipping'),
            ('delivered', 'Delivered'),
            ('cancelled', 'Cancelled'),
            ('return', 'Return'),
            ('partial_return', 'Partial Return')
        ],
        string='State',
        default='unknown',
        tracking=True
    )
    payment_state = fields.Selection(
        [
            ('pending', 'Pending'),
            ('waiting_confirmation', 'Waiting Confirmation'),
            ('paid', 'Paid'),
            ('failed', 'Failed'),
            ('pending_refund', 'Pending Refund'),
            ('refunded', 'Refunded')
        ],
        string='Payment State',
        default='pending',
        tracking=True
    )
    payment_method = fields.Selection(
        [
            ('unknown', 'Unknown'),
            ('account', 'Account'),
            ('card', 'Card'),
            ('transfer', 'Transfer'),
            ('paypal', 'Paypal'),
            ('bizum', 'Bizum'),
            ('others', 'Others')
        ],
        string='Payment Method',
        default='unknown'
    )
    amount_untaxed = fields.Float(
        string='Base Amount',
        digits='Product Price'
    )
    discount_percentage = fields.Float(string='Discount %')
    amount_discount = fields.Float(
        string='Discount',
        compute='_compute_amount_discount',
        store=True
    )
    amount_subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_amount_subtotal',
        store=True
    )
    amount_tax_percentage = fields.Float(string='VAT %')
    amount_tax = fields.Float(
        string='VAT',
        compute='_compute_amount_tax',
        store=True
    )
    amount_total = fields.Float(
        string='Total',
        compute='_compute_amount_total',
        store=True
    )
    date_modified = fields.Datetime(
        string='Modification Date',
        default=fields.Datetime.now
    )
    date_created = fields.Datetime(
        string='Creation Date',
        default=fields.Datetime.now
    )
    note = fields.Text(string='Notes')
    partner_invoice_id = fields.Many2one(
        comodel_name='res.partner',
        string='Billing Address',
        required=True
    )
    partner_shipping_id = fields.Many2one(
        comodel_name='res.partner',
        string='Shipping Address'
    )
    partner_origin_id = fields.Many2one(
        comodel_name='res.partner',
        string='Shipping Origin',
        required=True
    )
    store_pickup = fields.Boolean(string='Store Pickup')
    action_state = fields.Integer(string='Action State')
    information = fields.Text(string='Information')
    total_incidents = fields.Integer(
        string='Total Incidents',
        compute='_compute_incidents'
    )
    open_incidents = fields.Integer(
        string='Open Incidents',
        compute='_compute_incidents'
    )
    accounted = fields.Boolean(
        string='Accounted',
        default=False
    )
    crvnet_state = fields.Char(string='CRVNet State')
    sale_line_ids = fields.One2many(
        comodel_name='line.scrapyard.sale',
        inverse_name='sale_id',
        string='Lines'
    )
    document_ids = fields.One2many(
        comodel_name='sale.document',
        inverse_name='sale_id',
        string='Documents'
    )
    incident_ids = fields.One2many(
        comodel_name='incident.scrapyard.sale',
        inverse_name='sale_id',
        string='Incidents'
    )

    @api.depends('amount_untaxed', 'discount_percentage')
    def _compute_amount_discount(self):
        for sale in self:
            sale.amount_discount = sale.amount_untaxed * (sale.discount_percentage / 100)

    @api.depends('amount_untaxed', 'amount_discount')
    def _compute_amount_subtotal(self):
        for sale in self:
            sale.amount_subtotal = sale.amount_untaxed - sale.amount_discount

    @api.depends('amount_subtotal', 'amount_tax_percentage')
    def _compute_amount_tax(self):
        for sale in self:
            sale.amount_tax = sale.amount_subtotal * (sale.amount_tax_percentage / 100)

    @api.depends('amount_subtotal', 'amount_tax')
    def _compute_amount_total(self):
        for sale in self:
            sale.amount_total = sale.amount_subtotal + sale.amount_tax

    @api.depends('incident_ids', 'incident_ids.state')
    def _compute_incidents(self):
        for sale in self:
            sale.total_incidents = len(sale.incident_ids)
            sale.open_incidents = len(sale.incident_ids.filtered(lambda x: x.state == 'open'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.scrapyard.sequence') or 'New'
        return super().create(vals_list)
