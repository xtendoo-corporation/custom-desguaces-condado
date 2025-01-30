{
    'name': 'Metasync API Connector',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Conector API  con Metasync',
    'description': """
        Este módulo permite realizar peticiones a través de la API Metasync
        para sincronizar datos.
    """,
    'depends': ['stock'],
    'data': [
        'views/stock_picking_metasync_api_menu.xml',
        'views/product_category_views.xml',
        'views/product_template_only_form_view.xml',
        'wizards/recover_changes_stock_metasync_wizard_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
