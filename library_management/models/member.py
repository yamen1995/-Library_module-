from odoo import models, fields, api

class LibraryMember(models.Model):
    _name = 'library.member'
    _description = 'Library Member'
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    member_since = fields.Date(default=fields.Date.today)
    is_active_member = fields.Boolean(default=True)
    borrow_record_ids = fields.One2many('library.borrow', 'borrower_id', string='Borrow Records')

    books_borrowed = fields.Many2many('library.book', compute='_compute_books_borrowed', string='Borrowed Books')
    late_fees = fields.Many2many('account.move', compute='_compute_late_fees', string='Late Fees')

    @api.depends('borrow_record_ids.book_id')
    def _compute_books_borrowed(self):
        for member in self:
            member.books_borrowed = member.borrow_record_ids.mapped('book_id')

    @api.depends('borrow_record_ids.late_fee_invoice_id')
    def _compute_late_fees(self):
        for member in self:
            member.late_fees = member.borrow_record_ids.filtered(lambda r: r.has_invoice).mapped('late_fee_invoice_id')
