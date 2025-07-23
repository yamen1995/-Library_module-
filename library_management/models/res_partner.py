from odoo import models, fields, api
""""extending res.partner """
class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_library_member = fields.Boolean(string="Is Library Member", default=False)
    member_since = fields.Date(default=fields.Date.today)
    card_id = fields.Char(string="Card ID", readonly=True)

    borrow_record_ids = fields.One2many('library.borrow', 'borrower_id', string='Borrow Records')
    books_borrowed = fields.Many2many('library.book', compute='_compute_books_borrowed', string='Borrowed Books')
    late_fees = fields.Many2many('account.move', compute='_compute_late_fees', string='Late Fees')

    membership_count = fields.Integer(string="Memberships", compute="_compute_membership_count")

    @api.depends('borrow_record_ids.book_id')
    def _compute_books_borrowed(self):
        for rec in self:
            rec.books_borrowed = rec.borrow_record_ids.mapped('book_id')

    @api.depends('borrow_record_ids.late_fee_invoice_id')
    def _compute_late_fees(self):
        for rec in self:
            rec.late_fees = rec.borrow_record_ids.filtered(lambda r: r.has_invoice).mapped('late_fee_invoice_id')

    def _compute_membership_count(self):
        for rec in self:
            rec.membership_count = 1 if rec.is_library_member else 0

    def action_view_memberships(self):
        return {
            'name': 'Library Memberships',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'domain': [('id', '=', self.id), ('is_library_member', '=', True)],
            'context': {'default_is_library_member': True},
        }
