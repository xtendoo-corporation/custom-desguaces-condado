{
    'name': 'Desguace del Condado Website',
    'version': '18.0.1.0',
    'category': 'Website',
    'summary': 'Desguace del Condado Website',
    'description': """
        Este módulo introduce cambios en el sitio web de Desguace del Condado.
    """,
    'depends': [
        'website_sale',
        'metasync_api_connector'
        ],
    'data': [
        'views/product_price_inherit.xml'
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
