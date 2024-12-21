from odoo import models, fields, api
from odoo.exceptions import ValidationError
import math

import logging

_logger = logging.getLogger(__name__)

class IPBU(models.Model):
    """
    This model represents an IPBU (Cost Sheet), with fields for tracking various costs, sales, and suppliers related to a lead.
    The model also includes functionality for creating, confirming, and canceling IPBUs, as well as converting them into quotations.
    """
    _name = 'ipbu.ipbu'
    _description = 'IPBU Model'
    _rec_name = 'code'

    # Basic Fields
    name = fields.Text(string='IPBU Name', store=True, tracking=True, required=True)
    code = fields.Char(
        string='Cost Sheet Code',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('ipbu.code') or 'New'
    )
    date = fields.Date(string='Date', default=fields.Date.context_today, readonly=True)

    # Inheritance for mail tracking and activity mixin
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Relations to other models
    lead_id = fields.Many2one('crm.lead', string='Lead/Opportunity', tracking=True, required=True)
    product_line_ids = fields.One2many('ipbu.product.line', 'ipbu_id', string='Product Lines', tracking=True)

    # Computed Fields for total costs and sales
    total_cost_cac = fields.Float(string='CAC Cost', readonly=True, store=True, compute='_compute_total_cost_cac')
    total_sale_exw = fields.Float(string='EXW Sale', readonly=True, store=True, compute='_compute_total_sale_exw')
    total_origin_expenses = fields.Float(string='Origin Expenses', store=True, compute='_compute_total_origin_expenses')
    total_cost_custom = fields.Float(string='Custom Costs', readonly=True, store=True, compute='_compute_total_cost_custom')
    total_destination_expenses = fields.Float(string='Destination Expenses', readonly=True, store=True, compute='_compute_total_destination_expenses')
    total_logistics_margin = fields.Float(string='Logistics Margin', readonly=True, store=True, compute='_compute_total_logistics_margin')
    total_ddp = fields.Float(string='Total DDP', readonly=True, store=True, compute='_compute_total_ddp')
    margin = fields.Float(string='Base Margin', tracking=True)
    line_discount = fields.Float(string='Line Discount', tracking=True)
    local_utility = fields.Float(string='Local Utility', tracking=True)
    invoice_cac = fields.Float(string='CAC Invoice', readonly=True, store=True, compute='_compute_total_invoice_cac')
    utility_cac = fields.Float(string='CAC Utility', readonly=True, store=True, compute='_compute_total_utility_cac')
    
    # Category and Supplier Information
    category = fields.Selection([('Repuestos', 'Parts'), ('Equipos', 'Equipment')], string='Category', default='Equipos', tracking=True)
    companies = fields.Many2one('res.partner', string='CAC Group', tracking=True, required=True, domain=[('x_studio_cac_group', '=', True)])
    area = fields.Text(string='Area', store=True, compute='_compute_area')
    principal_supplier = fields.Text(string='Supplier', store=True, compute='_compute_principal_supplier')
    
    # Version and Invoice Company
    version = fields.Integer(string='Version', required=True, store=True, default="0")
    invoices_company = fields.Text(string='Invoicing Company', store=True, compute='_compute_invoices_company')

    # Status
    status = fields.Selection([('active', 'Active'), ('inactive', 'Inactive')], string='Status', default='inactive')

    # Constraints for uniqueness of code and name
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Cost sheet code must be unique.'),
        ('name_unique', 'unique(name)', 'IPBU name must be unique.')
    ]

    # Fields to track quotation and lead code
    has_quotation = fields.Boolean(string='Quotation Created', default=False, tracking=True)
    quotation_id = fields.Many2one('sale.order', string='Quotation')
    lead_code = fields.Text(string='Opportunity Code', store=True, compute='_compute_lead_code')

    # Action to confirm an IPBU (changing status to active)
    def action_confirm(self):
        if not self.lead_id:
            raise ValidationError("The opportunity assigned to this IPBU does not exist.")
            return

        # Check if an active IPBU already exists for the same lead
        ipbu_activo = self.search([
            ('lead_id', '=', self.lead_id.id),
            ('status', '=', 'active'),
            ('id', '!=', self.id)
        ])

        if ipbu_activo:
            raise ValidationError("This opportunity already has an active quotation, it must be deactivated first.")
            return

        self.status = 'active'

    # Action to cancel an IPBU (changing status to inactive)
    def action_cancel(self):
        self.status = 'inactive'

    # Action to convert the IPBU into a quotation
    def action_convert_to_quotation(self):
        SaleOrder = self.env['sale.order']
        SaleOrderLine = self.env['sale.order.line']
        
        # Create a new sale order based on the IPBU
        order_vals = {
            'partner_id': self.lead_id.partner_id.id,
            'date_order': fields.Date.today(),
            'origin': self.code,
            'state': 'draft',
            'opportunity_id': self.lead_id.id,
            'code': self.name
        }
        sale_order = SaleOrder.create(order_vals)

        # Create sale order lines based on IPBU product lines
        for product_line in self.product_line_ids:
            order_line_vals = {
                'order_id': sale_order.id,
                'product_id': product_line.product_id.id,
                'product_uom_qty': product_line.product_qty,
                'price_unit': product_line.quotation_total,
                'tax_id': [(6, 0, product_line.product_id.taxes_id.ids)],
            }
            SaleOrderLine.create(order_line_vals)

        self.quotation_id = sale_order
        self.message_post(body=f'IPBU {self.code} has been converted into quotation {sale_order.name}.')
        self.has_quotation = True

        return {
            'type': 'ir.actions.act_window',
            'name': 'Quotation',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_id': sale_order.id,
            'target': 'current',
        }

    # Computed field methods
    @api.depends('product_line_ids')
    def _compute_totals(self):
        for record in self:
            total_cost_cac = sum(line.cost_qty for line in record.product_line_ids)
            record.total_cost_cac = total_cost_cac

    @api.depends('product_line_ids')
    def _compute_total_sale_exw(self):
        for record in self:
            total_sale_exw = sum(line.sale_qty_exw for line in record.product_line_ids if line.sale_qty_exw)
            record.total_sale_exw = total_sale_exw

    @api.depends('product_line_ids')
    def _compute_total_origin_expenses(self):
        for record in self:
            if record.category == 'Equipos':
                total_origin = sum(line.origin_expenses for line in record.product_line_ids if line.origin_expenses)
                record.total_origin_expenses = total_origin

    @api.depends('product_line_ids')
    def _compute_total_cost_custom(self):
        for record in self:
            if record.category == 'Equipos':
                total_custom = sum(line.cost_custom for line in record.product_line_ids if line.cost_custom)
                record.total_cost_custom = total_custom

    @api.depends('product_line_ids')
    def _compute_total_destination_expenses(self):
        for record in self:
            if record.category == 'Equipos':
                total_destination = sum(line.destination_expenses for line in record.product_line_ids if line.destination_expenses)
                record.total_destination_expenses = total_destination

    @api.depends('product_line_ids')
    def _compute_total_cost_cac(self):
        for record in self:
            total_cac = sum(line.cost_qty for line in record.product_line_ids if line.cost_qty)
            record.total_cost_cac = total_cac

    @api.depends('product_line_ids')
    def _compute_total_invoice_cac(self):
        for record in self:
            total_invoice = sum(line.intern_price for line in record.product_line_ids if line.intern_price)
            record.invoice_cac = total_invoice

    @api.depends('product_line_ids')
    def _compute_total_utility_cac(self):
        for record in self:
            total_utility = sum(line.utility_cac for line in record.product_line_ids if line.utility_cac)
            record.utility_cac = total_utility

    @api.depends('total_cost_custom', 'total_destination_expenses')
    def _compute_total_logistics_margin(self):
        for record in self:
            total_logistics_margin = (record.total_cost_custom + record.total_destination_expenses) * 0.1
            record.total_logistics_margin = total_logistics_margin

    @api.depends('total_sale_exw', 'total_origin_expenses', 'total_cost_custom', 'total_destination_expenses', 'total_logistics_margin')
    def _compute_total_ddp(self):
        for record in self:
            total_ddp = record.total_sale_exw + record.total_origin_expenses + record.total_cost_custom + record.total_destination_expenses + record.total_logistics_margin
            record.total_ddp = total_ddp

    # Helper methods for computing area, lead code, invoices company, and principal supplier
    @api.depends('lead_id')
    def _compute_area(self):
        for record in self:
            if record.lead_id:
                first_character = record.lead_id.x_studio_area[:1].upper()
                record.area = first_character

    @api.depends('lead_id')
    def _compute_lead_code(self):
        for record in self:
            if record.lead_id:
                record.lead_code = record.lead_id.code
            else:
                record.lead_code = ''

    @api.depends('companies')
    def _compute_invoices_company(self):
        for record in self:
            if record.companies:
                record.invoices_company = record.companies.x_studio_abbreviation
            else:
                record.invoices_company = ''

    @api.depends('lead_id')
    def _compute_principal_supplier(self):
        for record in self:
            if record.lead_id:
                record.principal_supplier = record.lead_id.x_studio_main_supplier.x_studio_abbreviation
        return 

    # Overridden methods for creating and writing records
    @api.model
    def create(self, vals):
        record = super(IPBU, self).create(vals)
        record._update_first_product_flag()
        return record

    def write(self, vals):
        result = super(IPBU, self).write(vals)
        self._update_first_product_flag()
        return result

    # Onchange method to update first product flag
    @api.onchange('product_line_ids')
    def _update_first_product_flag(self):
        for record in self:
            if record.product_line_ids:
                for index, line in enumerate(record.product_line_ids):
                    if index == 0:
                        can_sum = False
                        total_sum = 0
                        utility_difference = line.utility - line.local_utility
                        local_utility_sum = 0
                        
                        for i, l in enumerate(line.ipbu_id.product_line_ids):
                            if l.local_buy == 'yes': 
                                can_sum = True
                            if i != 0:
                                total_sum += l.utility_cac
                            
                        local_utility_sum = total_sum if can_sum else 0

                        line.is_first_product = True
                        line.utility_cac = math.ceil(utility_difference + local_utility_sum)
                        line.supplier = line.product_id.x_studio_product_supplier.display_name
                        line.real_margin = self.margin
                        line.discount = self.line_discount

                        if record.category != "Repuestos":
                            continue

                        if (len(record.product_line_ids) > 1 and record.product_line_ids[index].product_cost != 0 and record.product_line_ids[index + 1].product_cost != 0):
                            total = sum(l.sale_qty_exw for l in record.product_line_ids if l.sale_qty_exw)
                            line.ponderado_incoterm = min(0.65, line.sale_qty_exw / total)
                        else:
                            line.ponderado_incoterm = 1
                    else:
                        line.is_first_product = False
                        line.utility_cac = math.ceil(line.utility - line.local_utility)
                        line.supplier = line.product_id.x_studio_product_supplier.display_name
                        line.real_margin = self.margin
                        line.discount = self.line_discount

                        if record.category != "Repuestos":
                            continue

                        total = 0
                        
                        for i, l in enumerate(record.product_line_ids):
                            if(i != 0):
                                total += l.sale_qty_exw

                        if (line.sale_qty_exw != 0 and total != 0):
                            line.ponderado_incoterm = (line.sale_qty_exw / total) * (1 - record.product_line_ids[0].ponderado_incoterm)

    # Action to view the created quotation
    def action_view_quotation(self):
        self.ensure_one()
        if self.quotation_id:
            return {
                'name': 'Quotation',
                'domain': [('id', '=', self.quotation_id.id)],
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'context': {'default_lead_id': self.lead_id.id},
            }
