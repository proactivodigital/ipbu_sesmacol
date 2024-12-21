from odoo import models, fields, api
from datetime import datetime

class SaleOrder(models.Model):
    _inherit = 'sale.order'  # Inherits from the existing 'sale.order' model

    # Adds a new field to the 'sale.order' model
    code = fields.Char(
        string='Code',  # The label for the field in the UI
        readonly=False,  # The field is not read-only, so it can be edited
        copy=False,  # The field will not be copied when a record is duplicated
        index=True,  # The field is indexed in the database for faster searching
        unique=True,  # Ensures that the values in this field are unique across all records
        required=True  # Makes this field mandatory when creating or editing a record
    )
