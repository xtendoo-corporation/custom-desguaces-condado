from odoo import models, fields, api

class AddressScrapyardSale(models.Model):
    _name = 'address.scrapyard.sale'
    _description = 'Address Scrapyard Sale'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    name = fields.Char(string='Description')
    seller_id = fields.Many2one(
        comodel_name='res.users',
        string='Seller',
        required=True
    )
    address_type = fields.Selection(
        selection=[
            ('billing', 'Billing'),
            ('shipping', 'Shipping'),
            ('shipping_origin', 'Shipping Origin')
        ],
        string='Address Type',
        required=True
    )
    vat = fields.Char(
        string='VAT',
        required=True
    )
    trade_name = fields.Char(
        string='Trade Name',
        required=True
    )
    company_name = fields.Char(
        string='Company Name',
        required=True
    )
    street = fields.Char(
        string='Street',
        required=True
    )
    state_code = fields.Char(string='State Code')
    state = fields.Char(
        string='State',
        required=True
    )
    city_code = fields.Char(string='City Code')
    city = fields.Char(
        string='City',
        required=True
    )
    zip = fields.Char(
        string='ZIP Code',
        required=True
    )
    country_code = fields.Char(string='Country Code')
    country = fields.Char(
        string='Country',
        required=True
    )
    email = fields.Char(
        string='Email',
        required=True
    )
    phone = fields.Char(
        string='Phone',
        required=True
    )
    mobile = fields.Char(string='Mobile')
    fax = fields.Char(string='Fax')
    notes = fields.Text(string='Notes')
