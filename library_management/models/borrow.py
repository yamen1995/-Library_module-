from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta, date

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta, date

class LibraryBorrow(models.Model):
    _name = 'library.borrow'
    _description = 'Borrowing Record'

    book_id = fields.Many2one(
        'library.book', string='Book', required=True,
        domain=[('is_available', '=', True)]
    )
    borrower_id = fields.Many2one(
        'res.partner', string='Borrower', required=True,
        domain=[('is_library_member', '=', True)]
    )
    card_id = fields.Char(string="Card ID", related='borrower_id.card_id', readonly=True)

    borrow_date = fields.Date(string='Borrow Date', default=fields.Date.today)
    return_date = fields.Date(string='Return Date')
    is_returned = fields.Boolean(string='Returned', default=False)
    late_fee_invoice_id = fields.Many2one('account.move', string="Late Fee Invoice", readonly=True, copy=False)
    has_invoice = fields.Boolean(compute='_compute_has_invoice', string="Invoice", store=True)

    borrow_state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Borrowed'),
        ('overdue', 'Overdue'),
        ('returned', 'Returned')
    ], string="Status", default='draft', store=True)

    due_countdown = fields.Char(string="Due In", compute="_compute_due_countdown")

    @api.onchange('borrow_date')
    def _onchange_borrow_date(self):
        if self.borrow_date:
            self.return_date = self.borrow_date + timedelta(days=7)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._validate_membership()

            # Book availability (set False) without triggering write() again
            if record.book_id and record.book_id.is_available:
                record.book_id.sudo().write({'is_available': False})

            record._compute_and_set_state()
        return records

    def write(self, vals):
        res = super().write(vals)

        # Only apply these if directly related fields were changed
        if 'borrower_id' in vals:
            for record in self:
                record._validate_membership()

        if 'book_id' in vals:
            for record in self:
                if record.book_id and record.book_id.is_available:
                    record.book_id.sudo().write({'is_available': False})

        # Don't recompute state unnecessarily (avoid loops)
        if not any(field in vals for field in ['borrow_state', 'is_returned']):
            self._compute_and_set_state()

        return res

    def _validate_membership(self):
        today = fields.Date.today()
        for record in self:
            memberships = self.env['library.membership.request'].search([
                ('partner_id', '=', record.borrower_id.id),
                ('status', '=', 'active'),
                ('request_date', '<=', today),
                ('end_date', '>=', today),
            ], limit=1)

            if not memberships:
                raise UserError("Borrower must have an active membership valid for today.")

    def _compute_and_set_state(self):
        today = fields.Date.today()
        for record in self:
            if record.is_returned:
                record.borrow_state = 'returned'
            elif record.return_date and record.return_date < today:
                record.borrow_state = 'overdue'
            elif record.book_id:
                record.borrow_state = 'confirmed'
            else:
                record.borrow_state = 'draft'

    def _compute_due_countdown(self):
        for rec in self:
            if rec.return_date and not rec.is_returned:
                days = (rec.return_date - date.today()).days
                if days > 0:
                    rec.due_countdown = f"{days} days left"
                elif days == 0:
                    rec.due_countdown = "Due today"
                else:
                    rec.due_countdown = f"Overdue by {abs(days)} days"
            else:
                rec.due_countdown = ""

    def _create_late_fee_invoice(self, amount):
        if not self.borrower_id:
            raise UserError("No borrower set. Cannot generate late fee invoice.")

        late_fee_product = self.env.ref('library_management.product_library_late_fee', raise_if_not_found=False)
        if not late_fee_product:
            raise UserError("Late fee product not configured. Please define a product with XML ID 'product_library_late_fee'.")

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.borrower_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': late_fee_product.id,
                'name': f'Late return fee for "{self.book_id.title}"',
                'quantity': 1,
                'price_unit': amount,
            })]
        }
        invoice = self.env['account.move'].create(invoice_vals)
        self.late_fee_invoice_id = invoice.id
        return invoice

    @api.depends('late_fee_invoice_id')
    def _compute_has_invoice(self):
        for record in self:
            record.has_invoice = bool(record.late_fee_invoice_id)

    def action_mark_returned(self):
        skipped = []
        for record in self:
            if record.is_returned:
                skipped.append(record.display_name)
                continue

            record.is_returned = True

            # Mark book as available
            if record.book_id:
                record.book_id.sudo().write({'is_available': True})

            # Generate late fee if overdue
            today = fields.Date.today()
            if record.return_date and today > record.return_date:
                late_days = (today - record.return_date).days
                total_fee = late_days * 2.0
                record._create_late_fee_invoice(total_fee)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Return Status",
                "message": (
                    "Some records were already returned: %s" % ", ".join(skipped)
                    if skipped else "Marked as returned successfully!"
                ),
                "type": "warning" if skipped else "success",
                "sticky": False,
                "next": {"type": "ir.actions.client", "tag": "reload"},
            }
        }