from odoo import models, fields, api
from datetime import timedelta
""""database model for membership requests """
class LibraryMembershipRequest(models.Model):
    _name = 'library.membership.request'
    _description = 'Library Membership Request'
    _order = 'request_date desc'

    name = fields.Char(string="Name", compute='_compute_name', store=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string="Member", required=True)
    request_date = fields.Date(default=fields.Date.today, string="Registration Date")
    end_date = fields.Date(string="End Date")
    card_id = fields.Char(related='partner_id.card_id', string="Card ID", readonly=True)
    payment_term_id = fields.Many2one('account.payment.term', string="Payment Terms")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('active', 'Active'),
    ], default='draft', string="Status")

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)

    membership_line_ids = fields.One2many('library.membership.line', 'request_id', string="Membership Lines")

    def action_confirm(self):
        self.write({'status': 'confirmed'})
    
    @api.depends('partner_id')
    def _compute_name(self):
        for record in self:
            if record.partner_id:
                record.name = f"{record.partner_id.name} Membership Request"
            else:
                record.name = "Membership Request"

    def action_generate_invoice(self):
        self.ensure_one()
        if not self.membership_line_ids:
            raise UserError("Please add at least one membership line.")

        invoice_lines = []
        for line in self.membership_line_ids:
            invoice_lines.append((0, 0, {
                'name': line.product_id.name,
                'quantity': 1,
                'price_unit': line.price_unit,
                'account_id': line.product_id.property_account_income_id.id or
                              line.product_id.categ_id.property_account_income_categ_id.id,
            }))

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_origin': self.name,
            'invoice_date': fields.Date.today(),
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': invoice_lines,
        })

        invoice.action_post()
        self.write({'invoice_id': invoice.id, 'status': 'paid'})

    def action_activate(self):
        self.write({'status': 'active'})
        self.partner_id.write({
            'is_library_member': True,
            'card_id': self.partner_id.card_id or self.env['ir.sequence'].next_by_code('library.member.card'),
        })
    
    @api.onchange('request_date')
    def _onchange_request_date(self):
        if self.request_date:
            self.end_date = self.request_date + timedelta(days=30)