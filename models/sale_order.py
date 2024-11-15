from odoo import models, fields, api
from datetime import datetime

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    code = fields.Char(string='Code', readonly=False, copy=False, index=True, unique=True, required=True)