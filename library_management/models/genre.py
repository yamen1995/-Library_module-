from odoo import models, fields

class LibraryGenre(models.Model):
    _name = 'library.genre'
    _description = 'Book Genre'

    name = fields.Char(string='Genre', required=True)
    book_ids = fields.One2many('library.book', 'genre_id', string='Books')
    _sql_constraints = [
        ('unique_genre_name', 'unique(name)', 'Genre name must be unique!')
    ]