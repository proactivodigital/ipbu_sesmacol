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

    date_from = fields.Integer(string='Tiempo de Entrega minimo', required=True)
    date_to = fields.Integer(string='Tiempo de Entrega maximo', required=True)
    policy_delivery = fields.Char(string='Términos de entrega', compute='_compute_policy_delivery', store=True)
    policy_pay = fields.Text(string='Términos de pago')
    warranty = fields.Text(string='Garantía', required=True)
    extended = fields.Text(string='Nota', required=True)
    valid    = fields.Integer(string='Validez', required=True)
    company_incoterm = fields.Text(string='Compañia')
    
    @api.depends('incoterm', 'incoterm_location')
    def _compute_policy_delivery(self):
        for record in self:
            if record.incoterm and record.incoterm_location:
                record.policy_delivery = f"{record.incoterm.code}, {record.incoterm_location}, Según incoterms® 2020"
            else:
                record.policy_delivery = ""