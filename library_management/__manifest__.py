{
    'name': 'Library Management',
    'version': '1.1',
    'summary': 'Manage books, authors, and borrowing records',
    'description': 'A simple Library Management system for Odoo.',
    'category': 'Uncategorized',
    'author': 'yamen',
    'depends': ['base', 'contacts', 'account'],
    'assets': {
    'web.assets_backend': [
        'library_management/static/src/css/library_styles.css',
        'library_management/static/src/js/library_book_list_renderer.js',
        
    ],
},
    'data': [
        'security/ir.model.access.csv',
        'data/product_data.xml',
        'data/sequence.xml',
        'views/library_book_views.xml',
        'views/library_author_views.xml',
        'views/library_borrow_views.xml',
        'views/library_genre_views.xml',
        'views/res_partner_view_inherit.xml',
        'views/library_membership_request_views.xml',
        'views/library_invoice_actions.xml',
        'views/library_invoice_menu.xml',
        'views/menu.xml',
        ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',

}
