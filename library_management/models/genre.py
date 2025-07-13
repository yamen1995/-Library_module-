from odoo import models, fields

class LibraryGenre(models.Model):
    '''Book Genre Model
    Represents a genre of books in the library.
    Each genre can have multiple books associated with it.
    The model includes a computed field to count the number of books
    associated with the genre and an action to view those books.
    '''
    _name = 'library.genre'
    _description = 'Book Genre'

    name = fields.Char(string='Genre', required=True) # Name of the genre
    book_ids = fields.One2many('library.book', 'genre_id', string='Books') # List of books in this genre
    _sql_constraints = [
        ('unique_genre_name', 'unique(name)', 'Genre name must be unique!')
    ] # Ensure genre names are unique
    book_count = fields.Integer(string="Book Count", compute="_compute_book_count") # Count of books in this genre

    def _compute_book_count(self):
        """Compute the number of books in this genre."""
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