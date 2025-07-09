from odoo import models, fields

class LibraryGenre(models.Model):
    _name = 'library.genre'
    _description = 'Book Genre'

    name = fields.Char(string='Genre', required=True)
    book_ids = fields.One2many('library.book', 'genre_id', string='Books')
    _sql_constraints = [
        ('unique_genre_name', 'unique(name)', 'Genre name must be unique!')
    ]
    book_count = fields.Integer(string="Book Count", compute="_compute_book_count")

    def _compute_book_count(self):
        for genre in self:
            genre.book_count = len(genre.book_ids)
    def action_view_books(self):
        """ Action to view books in this genre """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Books in Genre: %s' % self.name,
            'res_model': 'library.genre',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('library_management.view_library_genre_form_tree').id,
            'target': 'new',
        }