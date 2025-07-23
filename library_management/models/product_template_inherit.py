from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_library_membership = fields.Boolean(string="Library Membership Product")