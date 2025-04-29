{
    'name': 'Metasync API Connector',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Conector API  con Metasync',
    'description': """
        Este módulo permite realizar peticiones a través de la API Metasync
        para sincronizar datos.
    """,
    'depends': ['stock',
                'fleet',
                'website_sale',
                'web',
                'sale'],
    'data': [
        'views/stock_picking_metasync_api_menu.xml',
        'views/product_category_views.xml',
        'views/product_template_only_form_view.xml',
        'views/product_public_category_view.xml',
        'views/sale_order_views.xml',
        'wizards/recover_changes_stock_metasync_wizard_view.xml',
        'wizards/recover_changes_stock_company_metasync_wizard_view.xml',
        'wizards/send_order_metasync_wizard_view.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_frontend': [
             # 'metasync_api_connector/static/src/xml/snippets.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
