from odoo import models, fields, api
from odoo.exceptions import ValidationError

class LibraryBook(models.Model):
    ''' Library Book Model
    Represents books in the library management system.
    Each book can have an author, genre, and multiple recommendations.
    The model includes fields for title, description, publish date,
    availability status, and ISBN. It also includes methods for
    recommending books, checking ISBN validity, and quick borrowing.'''
    _name = 'library.book'
    _description = 'Library Book'
    _rec_name = 'title'

    title = fields.Char(string='Title', required=True)
    author_id = fields.Many2one('library.author', string='Author')
    description = fields.Text(string='Description')
    publish_date = fields.Date(string='Publish Date')
    is_available = fields.Boolean(string='Available', default=True)
    status_display = fields.Char(
        string="Status",
        compute="_compute_status_display",
        store=False
    )

    isbn = fields.Char(string='ISBN')
    genre_id = fields.Many2one('library.genre', string='Genre')
    
    recommended_book_ids = fields.Many2many(
        'library.book', string="Recommended Books", compute="_compute_recommended_books"
    )

    @api.depends('genre_id')
    def _compute_recommended_books(self):
        for record in self:
            if record.genre_id:
                record.recommended_book_ids = record.get_recommended_books()
            else:
                record.recommended_book_ids = False

    def get_recommended_books(self, limit=5):
        """ Recommend books in same genre, exclude self, only available books """
        return self.env['library.book'].search([
            ('id', '!=', self.id),
            ('genre_id', '=', self.genre_id.id),
            ('is_available', '=', True)
        ], limit=limit) if self.genre_id else self.env['library.book']

    @api.constrains('isbn')
    def _check_isbn(self):
        for record in self:
            if record.isbn:
                if not record.isbn.isdigit():
                    raise ValidationError("ISBN must contain only digits.")
                if len(record.isbn) not in (10, 13):
                    raise ValidationError("ISBN must be either 10 or 13 digits long.")


    def action_view_recommendations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Recommendations',
            'res_model': 'library.book',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('library_management.view_library_book_recommendations').id,
            'target': 'new',  # Opens in a pop-up
        }
    def action_quick_borrow(self):
        """Open Borrow form with current book pre-filled, only if available."""
        self.ensure_one()

        if not self.is_available:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Unavailable Book",
                    "message": f'"{self.title}" is currently not available for borrowing.',
                    "type": "warning",
                    "sticky": False,
                }
            }

        return {
            'type': 'ir.actions.act_window',
            'name': 'New Borrow',
            'res_model': 'library.borrow',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_book_id': self.id},
        }
    @api.depends('is_available')
    def _compute_status_display(self):
        for record in self:
            if record.is_available:
                record.status_display = "✅ Available"
            else:
                record.status_display = "❌ Unavailable"
