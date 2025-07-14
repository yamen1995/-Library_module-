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
    _inherits = {'res.partner': 'partner_id'} # Inherit from res.partner to link member to partner record
    # _inherits allows fields from res.partner to be accessed directly on library.member.
    # It also links the lifecycle (create, delete) of partner_id to the member record.

    _sql_constraints = [
        ('unique_partner_id', 'unique(partner_id)', 'Each partner can only be a library member once.')
    ] # Ensure each partner can only be a member once

    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade') # Link to the partner record
    member_since = fields.Date(default=fields.Date.today) # Date when the member joined the library
    is_active_member = fields.Boolean(default=True) # Indicates if the member is considered active for filtering or tagging.
    # Currently redundant with is_deleted_member, but allows flexible membership states.

    borrow_record_ids = fields.One2many('library.borrow', 'borrower_id', string='Borrow Records')
    is_deleted_member = fields.Boolean(default=False) # Indicates if the member is soft deleted
    books_borrowed = fields.Many2many('library.book', compute='_compute_books_borrowed', string='Borrowed Books') # List of books currently borrowed by the member
    late_fees = fields.Many2many('account.move', compute='_compute_late_fees', string='Late Fees') # List of late fee invoices associated with the member

    @api.depends('borrow_record_ids.book_id')
    def _compute_books_borrowed(self):
        """Compute the books borrowed by the member."""
        for member in self:
            member.books_borrowed = member.borrow_record_ids.mapped('book_id')

    @api.depends('borrow_record_ids.late_fee_invoice_id')
    def _compute_late_fees(self):
        """Compute the late fees for the member."""
        for member in self:
            member.late_fees = member.borrow_record_ids.filtered(lambda r: r.has_invoice).mapped('late_fee_invoice_id')

    def _get_library_tag(self):
        """Get or create the 'Library Member' tag."""
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
        """Soft delete the member by marking it as deleted and inactive.
        The associated contact (res.partner) is deactivated but borrow records and fees remain.
        This behavior is easy to change depending on future requirements.
        """
        self.is_deleted_member = True
        self.is_active_member = False
        #self.partner_id.active = False
        #this line was removed because it require res.partner fields to be mirrored into member to work safely which is an overkill for current logic
        self._sync_partner_tag()

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to ensure the partner tag is set correctly when creating members.
        """
        records = super().create(vals_list)
        records._sync_partner_tag()
        return records 

    def write(self, vals):
        """
        Override write to ensure the partner tag is synced when updating members.
        """
        res = super().write(vals)
        self._sync_partner_tag()
        return res

    def unlink(self):
        """
        Override unlink to prevent deletion of library members.
        """
        raise UserError("Library members cannot be deleted. Deactivate them instead.")