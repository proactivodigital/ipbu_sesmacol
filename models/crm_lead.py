from odoo import models, fields, api
from datetime import datetime

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    ipbu_count = fields.Integer(string="IPBU Count", compute='_compute_ipbu_count')
    code = fields.Char(string='Code', readonly=True, copy=False, index=True, unique=True)

    def _compute_ipbu_count(self):
        for lead in self:
            lead.ipbu_count = self.env['ipbu.ipbu'].search_count([('lead_id', '=', lead.id)])

    def action_view_ipbu(self):
        return {
            'name': 'IPBU',
            'domain': [('lead_id', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'ipbu.ipbu',
            'type': 'ir.actions.act_window',
            'context': {'default_lead_id': self.id},
        }

    @api.model
    def create(self, vals):
        # Generar el código solo si el tipo es 'opportunity'
        if vals.get('type') == 'opportunity':
            vals['code'] = self._generate_lead_code()
        return super(CrmLead, self).create(vals)

    def _generate_lead_code(self):
        """Genera el código único para oportunidades basándose en el año."""
        current_year = datetime.now().year
        year_suffix = str(current_year)[-2:]
        sequence_code = f'crm.lead.code.{year_suffix}'

        # Buscar o crear la secuencia
        seq = self.env['ir.sequence'].sudo().search([('code', '=', sequence_code)], limit=1)
        if not seq:
            seq = self.env['ir.sequence'].sudo().create({
                'name': f'CRM Lead Sequence {year_suffix}',
                'code': sequence_code,
                'padding': 4,
                'prefix': f'L{year_suffix}-',
            })

        return seq.next_by_id()

    def convert_opportunity(self, partner_id, user_ids=False, team_id=False):
        """Sobrescribir para generar el código al convertir a oportunidad."""
        result = super(CrmLead, self).convert_opportunity(partner_id, user_ids=user_ids, team_id=team_id)

        for lead in self:
            if lead.type == 'opportunity' and not lead.code:
                lead.code = lead._generate_lead_code()

        return result
