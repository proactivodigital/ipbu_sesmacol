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

    delivery_time = fields.Char(string='Tiempo de Entrega', required=True)
    incoterm_age = fields.Integer(string='Edad del Incoterm', required=True)
    policy_delivery = fields.Char(string='Tiempo de Entrega', required=True, compute='_compute_policy_delivery', store=True)
    

    @api.depends('incoterm', 'incoterm_location', 'incoterm_age')
    def _compute_policy_delivery(self):
        for record in self:
            if record.incoterm and record.incoterm_location and record.incoterm_age:
                record.policy_delivery = f"{record.incoterm.code}, {record.incoterm_location}, Según incoterms {record.incoterm_age}"
            else:
                record.policy_delivery = ""