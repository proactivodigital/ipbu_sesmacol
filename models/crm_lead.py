from odoo import models, fields, api
from datetime import datetime

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # A computed field that counts the related IPBUs for each lead.
    ipbu_count = fields.Integer(string="IPBU Count")

    # A unique code for each lead, generated when the lead type is 'opportunity'.
    code = fields.Char(string='Code', readonly=True, copy=False, index=True, unique=True)
