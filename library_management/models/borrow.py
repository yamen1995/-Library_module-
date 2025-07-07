from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta, date

class LibraryBorrow(models.Model):
    """Model representing a book borrowing record in the library."""
    _name = 'library.borrow'
    _description = 'Borrowing Record'

    # Fields
    book_id = fields.Many2one(
        'library.book', string='Book', required=True,
        domain=[('is_available', '=', True)]
    )
    borrower_id = fields.Many2one(
        'res.partner', string='Borrower', required=True
    )
    borrow_date = fields.Date(
        string='Borrow Date', default=fields.Date.today
    )
    return_date = fields.Date(string='Return Date')
    is_returned = fields.Boolean(string='Returned', default=False)
    late_fee_invoice_id = fields.Many2one('account.move', string="Late Fee Invoice", readonly=True, copy=False)
    has_invoice = fields.Boolean(compute='_compute_has_invoice', string="Invoice")

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirmed', 'Borrowed'),
            ('overdue', 'Overdue'),
            ('returned', 'Returned')
        ],
        string="Status", compute="_compute_state", store=True
    )

    due_countdown = fields.Char(
        string="Due In", compute="_compute_due_countdown"
    )

    @api.onchange('borrow_date')
    def _onchange_borrow_date(self):
        """
        Automatically set the return date to 7 days after the borrow date
        when the borrow date is changed.
        """
        if self.borrow_date:
            borrow_date_obj = fields.Date.from_string(self.borrow_date)
            return_date_obj = borrow_date_obj + timedelta(days=7)
            self.return_date = fields.Date.to_string(return_date_obj)

    @api.depends('borrow_date', 'return_date', 'is_returned')
    def _compute_state(self):
        """
        Compute the current state of the borrowing record:
        - 'returned' if the book is returned
        - 'overdue' if the return date has passed and not returned
        - 'confirmed' if the book is borrowed and not overdue
        - 'draft' otherwise
        """
        today = fields.Date.today()
        for record in self:
            if record.is_returned:
                record.state = 'returned'
            elif record.return_date and record.return_date < today:
                record.state = 'overdue'
            elif record.book_id:
                record.state = 'confirmed'
            else:
                record.state = 'draft'

    @api.depends('return_date', 'is_returned')
    def _compute_due_countdown(self):
        """
        Compute a human-readable countdown until the return date,
        or show how many days overdue the book is.
        """
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

    @api.model
    def create(self, vals_list):
        """
        Override create to process book availability when a borrow record is created.
        """
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        records = super(LibraryBorrow, self).create(vals_list)
        for record in records:
            record._process_borrow()
        return records

    def write(self, vals):
        """
        Override write to process book availability when the book is changed.
        """
        res = super().write(vals)
        if 'book_id' in vals:
            self._process_borrow()
        return res

    def _process_borrow(self):
        """
        Handles book availability logic on borrow.
        Raises an error if the book is already borrowed.
        """
        for record in self:
            if record.book_id and not record.book_id.is_available:
                raise UserError("Book is already borrowed!")
            if record.book_id:
                record.book_id.is_available = False

    def action_mark_returned(self):
        """
        Mark the borrowing record as returned.
        Shows a notification if some records were already returned.
        """
        skipped = []
        for record in self:
            if record.is_returned:
                skipped.append(record.display_name)
                continue
            record.is_returned = True
            record.book_id.is_available = True
        # Calculate late fee
        late_days = 0
        fee_per_day = 2.0 
        today = fields.Date.today()

        if record.return_date and today > record.return_date:
            late_days = (today - record.return_date).days

        if late_days > 0:
            total_fee = late_days * fee_per_day
            record._create_late_fee_invoice(total_fee)

        if skipped:
            message = "Some records were already returned: %s" % ", ".join(skipped)
            notif_type = "warning"
        else:
            message = "Marked as returned successfully!"
            notif_type = "success"

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Return Status",
                "message": message,
                "type": notif_type,
                "sticky": False,
            }
        }
    def _create_late_fee_invoice(self, amount):
        if not self.borrower_id:
            return

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.borrower_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': f'Late return fee for "{self.book_id.title}"',
                'quantity': 1,
                'price_unit': amount,
            })]
        }
        invoice = self.env['account.move'].create(invoice_vals)
        self.late_fee_invoice_id = invoice.id

    @api.depends('late_fee_invoice_id')
    def _compute_has_invoice(self):
        for record in self:
            record.has_invoice = bool(record.late_fee_invoice_id)
