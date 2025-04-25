from odoo import models, fields, api

class LineScrapyardSale(models.Model):
    _name = 'line.scrapyard.sale'
    _description = 'Line Scrapyard Sale'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    seller_id = fields.Many2one(
        comodel_name='res.users',
        string='Seller',
        required=True
    )
    sale_id = fields.Many2one(
        comodel_name='scrapyard.sale',
        string='Sale',
        required=True,
        ondelete='cascade'
    )
    reference = fields.Char(
        string='Reference'
    )
    description = fields.Char(
        string='Description',
        required=True
    )
    quantity = fields.Integer(
        string='Quantity',
        required=True,
        default=1
    )
    price = fields.Float(
        string='Price',
        digits='Product Price',
        required=True
    )
    base_amount = fields.Float(
        string='Base Amount',
        digits='Product Price',
        compute='_compute_base_amount',
        store=True
    )
    discount_percentage = fields.Float(
        string='Discount %',
        digits='Discount'
    )

    discount = fields.Float(
        string='Discount',
        digits='Product Price',
        compute='_compute_discount',
        store=True
    )
    subtotal = fields.Float(
        string='Subtotal',
        digits='Product Price',
        compute='_compute_subtotal',
        store=True
    )
    line_type = fields.Selection(
        selection=[
            ('free', 'Free'),
            ('part', 'Part'),
            ('route', 'Route')
        ],
        string='Line Type',
        required=True,
        default='part'
    )

    @api.depends('quantity', 'price')
    def _compute_base_amount(self):
        for line in self:
            line.base_amount = line.quantity * line.price

    @api.depends('base_amount', 'discount_percentage')
    def _compute_discount(self):
        for line in self:
            line.discount = line.base_amount * (line.discount_percentage / 100)

    @api.depends('base_amount', 'discount')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.base_amount - line.discount
