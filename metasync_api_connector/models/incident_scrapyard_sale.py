from odoo import models, fields, api


class IncidentScrapyardSale(models.Model):
    _name = 'incident.scrapyard.sale'
    _description = 'Incident Scrapyard Sale'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]
    _order = 'creation_date desc'

    seller_id = fields.Many2one(
        comodel_name='res.users',
        string='Seller',
        required=True
    )
    sale_id = fields.Many2one(
        comodel_name='scrapyard.sale',
        string='Order',
        required=True,
        ondelete='cascade'
    )
    customer_id = fields.Char(
        string='Customer ID',
        required=True
    )

    notes = fields.Text(
        string='Notes',
        required=True
    )
    incident_type = fields.Selection(
        selection=[
            ('delayed_sale', 'Delayed Sale'),
            ('cancellation_request', 'Cancellation Request'),
            ('invoice_request', 'Invoice Request'),
            ('defective_sale', 'Defective Sale'),
            ('general', 'General'),
            ('sideo_mediation', 'Sideo Mediation'),
            ('crvnet_incident', 'CRVNet Incident')
        ],
        string='Incident Type',
        required=True,
        tracking=True
    )
    state = fields.Selection(
        [
            ('pending', 'Pending'),
            ('tracking', 'Tracking'),
            ('resolved', 'Resolved')
        ],
        string='State',
        required=True,
        default='pending',
        tracking=True
    )
    title = fields.Char(
        string='Title',
        required=True
    )
    creation_date = fields.Datetime(
        string='Creation Date',
        required=True,
        default=fields.Datetime.now
    )
    modification_date = fields.Datetime(
        string='Modification Date',
        required=True,
        default=fields.Datetime.now
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['modification_date'] = fields.Datetime.now()
        return super().create(vals_list)

    def write(self, vals):
        vals['modification_date'] = fields.Datetime.now()
        return super().write(vals)
