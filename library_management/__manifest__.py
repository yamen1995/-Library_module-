{
    'name': 'Library Management',
    'version': '1.0',
    'summary': 'Manage books, authors, and borrowing records',
    'description': 'A simple Library Management system for Odoo.',
    'category': 'Uncategorized',
    'author': 'yamen',
    'depends': ['base', 'contacts', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/library_book_views.xml',
        'views/library_author_views.xml',
        'views/library_borrow_views.xml',
        'views/library_genre_views.xml',
        'views/menu.xml',
        ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
    'assets': {
    'web.assets_backend': [
        'library_management/static/src/css/library_styles.css'
        ,
    ],
},
}
