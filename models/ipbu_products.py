from odoo import models, fields, api
import math
import logging

_logger = logging.getLogger(__name__)

class IPBUProductLine(models.Model):
    # Defines the 'ipbu.product.line' model, representing a product line in IPBU (possibly an abbreviation for a specific business process).
    _name = 'ipbu.product.line'
    _description = 'Product Line in IPBU'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Inherits email thread and activity mixin to track messages and activities on this model.

    # Fields definition
    ipbu_id = fields.Many2one('ipbu.ipbu', string='IPBU', required=False, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=False)
    product_qty = fields.Float(string='Quantity', required=False, store=True, tracking=True)
    product_cost = fields.Float(string='Product Cost', required=False, store=True, tracking=True)
    product_description = fields.Text(string='Description', store=True, tracking=True, compute='_compute_description')
    local_buy = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Local Purchase?', default="no", required=False, store=True, tracking=True)
    delivery_time = fields.Float(string='Factory Delivery Time', required=False, store=True, tracking=True)
    origin_expenses = fields.Float(string='Origin Expenses', required=False, store=True, tracking=True, compute='_compute_origin_expenses')
    cost_custom = fields.Float(string='Custom Costs', required=False, store=True, tracking=True, compute='_compute_cost_custom')
    destination_expenses = fields.Float(string='Destination Expenses', required=False, store=True, tracking=True, compute='_compute_destination_expenses')
    cost = fields.Float(string='Unit Cost', required=False, readonly=True, store=True, compute='_compute_cost')
    cost_qty = fields.Float(string='Total Cost', required=False, store=True, compute='_compute_cost_qty', tracking=True)
    sale_exw = fields.Float(string='EXW Sale Price', required=False, readonly=True, store=True, compute='_compute_sale_exw')
    sale_qty_exw = fields.Float(string='EXW Sale Price per Quantity', required=False, readonly=True, store=True, compute='_compute_sale_qty_exw')
    ponderado_incoterm = fields.Float(string='Incoterm Weight', required=False, compute='_compute_ponderado_incoterm', store=True, readonly=True)
    logistic_margin = fields.Float(string='Logistic Margin', required=False, compute='_compute_logistic_margin', store=True, readonly=True)
    DDP_value = fields.Float(string='DDP Unit Value', required=False, compute='_compute_DDP_value', store=True, readonly=True)
    quotation_total = fields.Float(string='Quotation Total', required=False, compute='_compute_quotation_total', store=True, readonly=True)
    utility = fields.Float(string='Utility', required=False, compute='_compute_utility', store=True, readonly=True)
    local_utility = fields.Float(string='Local Utility', compute='_compute_local_utility', required=False, store=True, readonly=True)
    local = fields.Float(string='Local Value', required=False, compute='_compute_local', store=True, readonly=True)
    local_cant = fields.Float(string='Local Value per Quantity', compute='_compute_local_cant', required=False, store=True, readonly=True)
    local_incoterm = fields.Float(string='Incoterm Value', compute='_compute_local_incoterm', required=False, store=True, readonly=True)
    total_customer = fields.Float(string='Total Customer Value', compute='_compute_total_customer', required=False, store=True, readonly=True)
    DDP_unit = fields.Float(string='DDP Unit', compute='_compute_DDP_unit', required=False, store=True, readonly=True)
    DDP_total = fields.Float(string='DDP Total', compute='_compute_DDP_total', required=False, store=True, readonly=True)
    is_first_product = fields.Boolean(default=False, required=False, store=True, readonly=True)
    utility_cac = fields.Float(string='Utility (CAC)', required=False, store=True, readonly=True)
    cac = fields.Float(string='CAC', compute='_compute_cac', required=False, store=True, readonly=True)
    cac_cant = fields.Float(string='CAC per Quantity', compute='_compute_cac_cant', required=False, store=True, readonly=True)
    incoterm_cac = fields.Float(string='Incoterm CAC', compute='_compute_incoterm_cac', required=False, store=True, readonly=True)
    intern_price = fields.Float(string='Internal Invoice Price', compute='_compute_intern_price', required=False, store=True, readonly=True)
    real_margin = fields.Float(string='Real Margin', compute='_compute_real_margin', default="0.0", required=False, store=True, readonly=False, tracking=True)
    supplier = fields.Text(string='Supplier', store=True, tracking=True)
    discount = fields.Float(string='Discount', compute='_compute_discount', default="0.0", required=False, store=True, readonly=False, tracking=True)
    category = fields.Text(string='Category', store=True, tracking=True, required=False, readonly=False, compute='_compute_category')

    # Compute methods
    @api.depends('origin_expenses', 'cost_custom', 'destination_expenses', 'ipbu_id.total_origin_expenses', 'ipbu_id.total_cost_custom', 'ipbu_id.total_destination_expenses')
    def _compute_ponderado_incoterm(self):
        """Computes the weighted incoterm value based on origin, custom, and destination expenses."""
        for line in self:
            total_origin_expenses = line.ipbu_id.total_origin_expenses
            total_cost_custom = line.ipbu_id.total_cost_custom
            total_destination_expenses = line.ipbu_id.total_destination_expenses

            divisor = total_origin_expenses + total_cost_custom + total_destination_expenses
            if divisor != 0:
                line.ponderado_incoterm = (line.origin_expenses + line.cost_custom + line.destination_expenses) / divisor
            else:
                line.ponderado_incoterm = 0.0

    def _compute_real_margin(self):
        """Computes the real margin."""
        return
    
    def _compute_discount(self):
        """Computes the discount value."""
        return

    @api.depends('cost_custom', 'destination_expenses')
    def _compute_logistic_margin(self):
        """Computes the logistic margin based on custom and destination expenses."""
        for line in self:
            line.logistic_margin = math.ceil((line.cost_custom + line.destination_expenses) * 0.1)

    @api.depends('origin_expenses', 'cost_custom', 'destination_expenses', 'sale_exw', 'logistic_margin')
    def _compute_quotation_total(self):
        """Computes the total quotation value based on various costs and margins."""
        for line in self:
            line.quotation_total = math.ceil(line.origin_expenses + line.cost_custom + line.destination_expenses + line.sale_qty_exw + line.logistic_margin)

    @api.depends('quotation_total', 'product_qty')
    def _compute_DDP_value(self):
        """Computes the DDP value per product based on the total quotation and quantity."""
        for line in self:
            if line.quotation_total <= 0 or line.product_qty <= 0:
                line.DDP_value = 0.0
            else:
                line.DDP_value = math.ceil(line.quotation_total / line.product_qty)

    @api.depends('quotation_total', 'origin_expenses', 'cost_custom', 'destination_expenses', 'logistic_margin', 'cost_qty')
    def _compute_utility(self):
        """Computes the utility value by subtracting costs from the quotation total."""
        for line in self:
            line.utility = math.ceil(line.quotation_total - line.origin_expenses - line.cost_custom - line.destination_expenses - line.logistic_margin - line.cost_qty)

    @api.depends('ipbu_id.line_discount', 'product_cost')
    def _compute_cost(self):
        """Computes the unit cost of the product, considering any discounts from the parent IPBU."""
        for line in self:
            if line.product_cost <= 0:
                line.cost = 0.0
            else:
                line.cost = math.ceil(line.product_cost * (1 - line.ipbu_id.line_discount))

    @api.depends('cost', 'product_qty')
    def _compute_cost_qty(self):
        """Computes the total cost based on the unit cost and quantity."""
        for line in self:
            if line.cost <= 0:
                line.cost_qty = 0.0
            else:
                line.cost_qty = math.ceil(line.cost * line.product_qty)

    @api.depends('cost', 'real_margin')
    def _compute_sale_exw(self):
        """Computes the EXW sale price considering the unit cost and margin."""
        for line in self:
            if line.cost <= 0:
                line.sale_exw = 0.0
            else:
                line.sale_exw = math.ceil(line.cost / (1 - line.real_margin))

    @api.depends('sale_exw', 'product_qty')
    def _compute_sale_qty_exw(self):
        """Computes the EXW sale price per quantity."""
        for line in self:
            if line.sale_exw <= 0:
                line.sale_qty_exw = 0.0
            else:
                line.sale_qty_exw = math.ceil(line.sale_exw * line.product_qty)

    @api.depends('quotation_total', 'ipbu_id.local_utility')
    def _compute_local_utility(self):
        """Computes the local utility based on the quotation total and local utility factor from the parent IPBU."""
        for line in self:
            if line.quotation_total <= 0 or line.ipbu_id.local_utility <= 0:
                line.local_utility = 0.0
            else:
                line.local_utility = line.quotation_total * line.ipbu_id.local_utility

    @api.depends('intern_price', 'product_qty', 'local_utility')
    def _compute_local(self):
        """Computes the local value considering the internal price, quantity, and local utility."""
        for line in self:
            if line.local_utility <= 0 or line.intern_price <= 0 or line.product_qty <= 0:
                line.local = 0.0
            else:
                line.local = math.ceil((line.intern_price / line.product_qty) + (line.local_utility / line.product_qty))

    @api.depends('local', 'product_qty')
    def _compute_local_cant(self):
        """Computes the local value per quantity."""
        for line in self:
            if line.local <= 0:
                line.local_cant = 0.0
            else:
                line.local_cant = math.ceil(line.local * line.product_qty)

    @api.depends('cost_custom', 'destination_expenses', 'logistic_margin')
    def _compute_local_incoterm(self):
        """Computes the incoterm value for local expenses based on category and total expenses."""
        for line in self:
            if line.category == 'Equipos':
                line.local_incoterm = math.ceil(line.cost_custom + line.destination_expenses + line.logistic_margin)
            else:
                sum_total = line.ipbu_id.total_cost_custom + line.ipbu_id.total_destination_expenses + line.ipbu_id.total_logistics_margin
                division = sum(line.local_cant for line in line.ipbu_id.product_line_ids)

                if division <= 0:
                    line.local_incoterm = 0
                else:
                    line.local_incoterm = ((sum_total) * line.local_cant) / division

    @api.depends('local_incoterm', 'local_cant')
    def _compute_total_customer(self):
        """Computes the total customer value considering the local incoterm and quantity."""
        for line in self:
            line.total_customer = math.ceil(line.local_incoterm + line.local_cant)

    @api.depends('total_customer', 'product_qty')
    def _compute_DDP_unit(self):
        """Computes the DDP unit price based on the total customer value and quantity."""
        for line in self:
            if line.total_customer <= 0 or line.product_qty <= 0:
                line.DDP_unit = 0.0
            else:
                line.DDP_unit = math.ceil(line.total_customer / line.product_qty)
    
    @api.depends('DDP_unit', 'product_qty')
    def _compute_DDP_total(self):
        """Computes the total DDP price by multiplying DDP unit price by quantity."""
        for line in self:
            if line.DDP_unit <= 0:
                line.DDP_total = 0.0
            else:
                line.DDP_total = math.ceil(line.DDP_unit * line.product_qty)

    @api.depends('cost', 'utility_cac', 'product_qty')
    def _compute_cac(self):
        """Computes the CAC (Customer Acquisition Cost) per unit based on product cost and utility."""
        for line in self:
            if line.product_qty <= 0:
                line.cac = 0.0
            else:
                line.cac = math.ceil((line.cost + line.utility_cac) / line.product_qty)

    @api.depends('cac', 'product_qty')
    def _compute_cac_cant(self):
        """Computes the total CAC cost based on quantity."""
        for line in self:
            if line.product_qty <= 0:
                line.cac_cant = 0.0
            else:
                line.cac_cant = math.ceil(line.cac * line.product_qty)
    
    @api.depends('origin_expenses', 'cac_cant')
    def _compute_incoterm_cac(self):
        """Computes the incoterm for CAC based on category and total origin expenses."""
        for line in self:
            if line.category == "Repuestos":
                cac_cant_sum = sum(line.cac_cant for line in line.ipbu_id.product_line_ids)
                if cac_cant_sum > 0:
                    line.incoterm_cac = (line.ipbu_id.total_origin_expenses * line.cac_cant) / cac_cant_sum
                else:
                    line.incoterm_cac = 0
            else:
                line.incoterm_cac = line.origin_expenses

    @api.depends('cac_cant', 'incoterm_cac')
    def _compute_intern_price(self):
        """Computes the internal invoice price considering the CAC and incoterm values."""
        for line in self:
            line.intern_price = math.ceil(line.cac_cant + line.incoterm_cac)

    @api.depends('ponderado_incoterm')
    def _compute_origin_expenses(self):
        """Computes the origin expenses based on the pondered incoterm."""
        for line in self:
            if line.ipbu_id.category == 'Repuestos':
                line.origin_expenses = line.ponderado_incoterm * 0.25
            else:
                line.origin_expenses = line.ponderado_incoterm * 0.15

    @api.depends('cost_custom', 'product_qty')
    def _compute_category(self):
        """Computes the category based on product cost and other factors."""
        for line in self:
            if line.product_cost > 0 and line.product_qty > 10:
                line.category = 'Equipos'
            else:
                line.category = 'Repuestos'
