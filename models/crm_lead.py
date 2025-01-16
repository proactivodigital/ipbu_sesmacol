from odoo import models, fields, api
from datetime import datetime

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # A computed field that counts the related IPBUs for each lead.
    ipbu_count = fields.Integer(string="IPBU Count", compute='_compute_ipbu_count')

    # A unique code for each lead, generated when the lead type is 'opportunity'.
    code = fields.Char(string='Code', readonly=False, copy=False, index=True, unique=True)

    # Computes the count of IPBUs related to each CRM lead.
    def _compute_ipbu_count(self):
        for lead in self:
            lead.ipbu_count = self.env['ipbu.ipbu'].search_count([('lead_id', '=', lead.id)])

    # Action to view the related IPBUs in a tree and form view.
    def action_view_ipbu(self):
        return {
            'name': 'IPBU',  # Name of the window
            'domain': [('lead_id', '=', self.id)],  # Filters to show only IPBUs related to the current lead
            'view_type': 'form',
            'view_mode': 'tree,form',  # Display both tree and form views
            'res_model': 'ipbu.ipbu',  # Model to open
            'type': 'ir.actions.act_window',
            'context': {'default_lead_id': self.id},  # Sets the lead_id in the context for the new record
        }

    # Overrides the create method to generate a unique code when creating an opportunity.
    @api.model
    def create(self, vals):
        # Generate the code only if the lead type is 'opportunity'
        if vals.get('type') == 'opportunity':
            vals['code'] = self._generate_lead_code()
        return super(CrmLead, self).create(vals)

    # Overrides the convert_opportunity method to generate the code when converting to an opportunity.
    def convert_opportunity(self, partner_id, user_ids=False, team_id=False):
        """Override to generate the code when converting to opportunity."""
        result = super(CrmLead, self).convert_opportunity(partner_id, user_ids=user_ids, team_id=team_id)

        return result