from odoo import models, fields
"""" database model for membership lines """
class LibraryMembershipLine(models.Model):
    _name = 'library.membership.line'
    _description = 'Library Membership Line'

    request_id = fields.Many2one('library.membership.request', string="Membership Request", required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Product", domain="[('sale_ok', '=', True), ('is_library_membership', '=', True)]", required=True)
    price_unit = fields.Monetary(string="Price", required=True)
    currency_id = fields.Many2one('res.currency', related='request_id.currency_id', store=True, readonly=False)