from odoo.exceptions import UserError
from odoo import models, fields, api

class LibraryMember(models.Model):
    ''' Library Member Model
    inherits from res.partner and
    Represents members of the library who can borrow books.
    Each member is linked to a partner record and can have multiple borrow records.
    The model includes fields for member since date, active status, and computed fields
    '''
    _name = 'library.member'
    _description = 'Library Member'
    _inherits = {'res.partner': 'partner_id'}
    _sql_constraints = [
        ('unique_partner_id', 'unique(partner_id)', 'Each partner can only be a library member once.')
    ]

    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    member_since = fields.Date(default=fields.Date.today)
    is_active_member = fields.Boolean(default=True)
    borrow_record_ids = fields.One2many('library.borrow', 'borrower_id', string='Borrow Records')
    is_deleted_member = fields.Boolean(default=False)
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

    def _get_library_tag(self):
        tag_xmlid = 'library.partner_category_library_member'
        tag = self.env.ref(tag_xmlid, raise_if_not_found=False)
        if not tag:
            # Try to find by name before creating
            tag = self.env['res.partner.category'].search([('name', '=', 'Library Member')], limit=1)
            if not tag:
                tag = self.env['res.partner.category'].create({'name': 'Library Member'})
        return tag

    def _sync_partner_tag(self):
        """Add/remove 'Library Member' tag based on is_active_member"""
        tag = self._get_library_tag()
        if not tag:
            return

        for member in self:
            if member.partner_id.active and member.is_active_member:
                if tag not in member.partner_id.category_id:
                    member.partner_id.category_id |= tag
            else:
                if tag in member.partner_id.category_id:
                    member.partner_id.category_id -= tag

    def action_soft_delete(self):
        self.is_deleted_member = True
        self.is_active_member = False
        self.partner_id.active = False
        self._sync_partner_tag()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_partner_tag()
        return records  # Fixed typo

    def write(self, vals):
        res = super().write(vals)
        self._sync_partner_tag()
        return res

    def unlink(self):
        raise UserError("Library members cannot be deleted. Deactivate them instead.")