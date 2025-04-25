from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import QueryURL, WebsiteSale


class CustomWebsiteForm(WebsiteSale):
    @http.route(['/contactus', '/contactus/<path:path>'], type='http', auth='public', website=True)
    def contactus(self, **kwargs):
        values = {}

        # Get URL parameters
        if request.params.get('subject'):
            values['subject'] = request.params.get('subject')

        if request.params.get('vehicle_id'):
            values['vehicle_id'] = request.params.get('vehicle_id')
            values['description'] = f"Query about vehicle #{values['vehicle_id']}"

        print("*"*80)
        print("Values obtained from URL:", values)

        response = super(CustomWebsiteForm, self).contactus(**kwargs)

        # If it's a dictionary, update with our values
        if isinstance(response, dict):
            response.update(values)

        return response
