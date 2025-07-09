from odoo import models, fields

class LibraryAuthor(models.Model):
    _name = 'library.author'
    _description = 'Library Author'

    name = fields.Char(string='Name', required=True)
    book_ids = fields.One2many('library.book', 'author_id', string='Books')
    book_count = fields.Integer(string="Book Count", compute="_compute_book_count")

    def _compute_book_count(self):
        for author in self:
            author.book_count = len(author.book_ids)
    def action_view_books(self):
        """ Action to view books by this author """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Books by Author: %s' % self.name,
            'res_model': 'library.author',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('library_management.view_library_author_form_tree').id,
            'target': 'new',
        }