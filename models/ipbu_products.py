from odoo import models, fields, api
import math
import logging

_logger = logging.getLogger(__name__)

class IPBUProductLine(models.Model):
    _name = 'ipbu.product.line'
    _description = 'Línea de Producto en ipbu'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    ipbu_id = fields.Many2one('ipbu.ipbu', string='ipbu', required=False, ondelete='cascade')
    product_id = fields.Many2one('product.template', string='Producto', required=False)
    product_qty = fields.Float(string='Cantidad', required=False, store=True, tracking=True)
    product_cost = fields.Float(string='Costo producto', required=False, store=True, tracking=True)
    product_description = fields.Text(string='Descripción', store=True, tracking=True, compute='_compute_description')
    local_buy = fields.Selection([
        ('yes', 'Sí'),
        ('no', 'No'),
    ], string='¿Compra Local?', default="no", required=False, store=True, tracking=True)
    delivery_time = fields.Float(string='Tiempo de entrega fábrica', required=False, store=True, tracking=True)
    origin_expenses = fields.Float(string='Gastos origen', required=False, store=True, tracking=True, compute='_compute_origin_expenses')
    cost_custom = fields.Float(string='Aduana', required=False, store=True, tracking=True, compute='_compute_cost_custom')
    destination_expenses = fields.Float(string='Gastos destino', required=False, store=True, tracking=True, compute='_compute_destination_expenses')
    cost = fields.Float(string='Costo unitario', required=False, readonly=True, store=True, compute='_compute_cost')
    cost_qty = fields.Float(string='Costo total', required=False, store=True, compute='_compute_cost_qty', tracking=True)
    sale_exw = fields.Float(string='Precio venta EXW', required=False, readonly=True, store=True, compute='_compute_sale_exw')
    sale_qty_exw = fields.Float(string='Precio venta EXW cant', required=False, readonly=True, store=True, compute='_compute_sale_qty_exw')
    ponderado_incoterm = fields.Float(string='Ponderado incoterm', required=False, compute='_compute_ponderado_incoterm', store=True, readonly=True)
    logistic_margin = fields.Float(string='Margen logístico', required=False, compute='_compute_logistic_margin', store=True, readonly=True)
    DDP_value = fields.Float(string='Valor DDP unitario', required=False, compute='_compute_DDP_value', store=True, readonly=True)
    quotation_total = fields.Float(string='Valor total cotización', required=False, compute='_compute_quotation_total', store=True, readonly=True)
    utility = fields.Float(string='Utilidad', required=False, compute='_compute_utility', store=True, readonly=True)
    local_utility = fields.Float(string='Utilidad local', compute='_compute_local_utility', required=False, store=True, readonly=True)
    local = fields.Float(string='Local', required=False, compute='_compute_local', store=True, readonly=True)
    local_cant = fields.Float(string='Local por cantidad', compute='_compute_local_cant', required=False, store=True, readonly=True)
    local_incoterm = fields.Float(string='Valor incoterm', compute='_compute_local_incoterm', required=False, store=True, readonly=True)
    total_customer = fields.Float(string='Total cliente', compute='_compute_total_customer', required=False, store=True, readonly=True)
    DDP_unit = fields.Float(string='DDP unitario', compute='_compute_DDP_unit', required=False, store=True, readonly=True)
    DDP_total = fields.Float(string='DDP total', compute='_compute_DDP_total', required=False, store=True, readonly=True)
    is_first_product = fields.Boolean(default=False, required=False, store=True, readonly=True)
    utility_cac = fields.Float(string='Utilidad', compute='_compute_utility_cac', required=False, store=True, readonly=True)
    cac = fields.Float(string='CAC', compute='_compute_cac', required=False, store=True, readonly=True)
    cac_cant = fields.Float(string='CAC por cantidad', compute='_compute_cac_cant', required=False, store=True, readonly=True)
    incoterm_cac = fields.Float(string='Incoterm', compute='_compute_incoterm_cac', required=False, store=True, readonly=True)
    intern_price = fields.Float(string='Factura interna', compute='_compute_intern_price', required=False, store=True, readonly=True)
    real_margin = fields.Float(string='Margen Real', compute='_compute_real_margin', default="0.0", required=False, store=True, readonly=False, tracking=True)
    supplier = fields.Text(string='Proveedor', store=True, tracking=True)
    discount = fields.Float(string='Descuento', compute='_compute_discount', default="0.0", required=False, store=True, readonly=False, tracking=True)
    category = fields.Text(string='Category', store=True, tracking=True, required=False, readonly=False, compute='_compute_category')

    @api.depends('origin_expenses', 'cost_custom', 'destination_expenses', 'ipbu_id.total_origin_expenses', 'ipbu_id.total_cost_custom', 'ipbu_id.total_destination_expenses')
    def _compute_ponderado_incoterm(self):
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
        return
    
    def _compute_discount(self):
        return

    @api.depends('cost_custom', 'destination_expenses')
    def _compute_logistic_margin(self):
        for line in self:
            line.logistic_margin = math.ceil((line.cost_custom + line.destination_expenses) * 0.1)

    @api.depends('origin_expenses', 'cost_custom', 'destination_expenses', 'sale_exw', 'logistic_margin')
    def _compute_quotation_total(self):
        for line in self:
            line.quotation_total = math.ceil(line.origin_expenses + line.cost_custom + line.destination_expenses + line.sale_qty_exw + line.logistic_margin)

    @api.depends('quotation_total', 'product_qty')
    def _compute_DDP_value(self):
        for line in self:
            if line.quotation_total <= 0 or line.product_qty <= 0 or line.product_qty <= 0:
                line.DDP_value = 0.0
            else:
                line.DDP_value = math.ceil(line.quotation_total / line.product_qty)

    @api.depends('quotation_total', 'origin_expenses', 'cost_custom', 'destination_expenses', 'logistic_margin', 'cost_qty')
    def _compute_utility(self):
        for line in self:
            line.utility = math.ceil(line.quotation_total - line.origin_expenses - line.cost_custom - line.destination_expenses - line.logistic_margin - line.cost_qty)

    @api.depends('ipbu_id.line_discount', 'product_cost')
    def _compute_cost(self):
        for line in self:
            if line.product_cost <= 0 or line.product_cost <= 0:
                line.cost = 0.0
            else:
                line.cost = math.ceil(line.product_cost * (1 - line.ipbu_id.line_discount))

    @api.depends('cost', 'product_qty')
    def _compute_cost_qty(self):
        for line in self:
            if line.cost <= 0 or line.cost <= 0:
                line.cost_qty = 0.0
            else:
                line.cost_qty = math.ceil(line.cost * line.product_qty)

    @api.depends('cost', 'real_margin')
    def _compute_sale_exw(self):
        for line in self:
            if line.cost <= 0 or line.cost <= 0:
                line.sale_exw = 0.0
            else:
                line.sale_exw = math.ceil(line.cost / (1 - line.real_margin))

    @api.depends('sale_exw', 'product_qty')
    def _compute_sale_qty_exw(self):
        for line in self:
            if line.sale_exw <= 0 or line.sale_exw <= 0:
                line.sale_qty_exw = 0.0
            else:
                line.sale_qty_exw = math.ceil(line.sale_exw * line.product_qty)

    @api.depends('quotation_total', 'ipbu_id.local_utility')
    def _compute_local_utility(self):
        for line in self:
            if line.quotation_total <= 0 or line.quotation_total <= 0:
                line.local_utility = 0.0
            else:
                line.local_utility = math.ceil(line.quotation_total * line.ipbu_id.local_utility)

    @api.depends('intern_price', 'product_qty', 'local_utility')
    def _compute_local(self):
        for line in self:
            if line.local_utility <= 0 or line.local_utility <= 0 or line.intern_price <= 0 or line.product_qty <= 0:
                line.local = 0.0
            else:
                line.local = math.ceil((line.intern_price / line.product_qty) + (line.local_utility / line.product_qty))

    @api.depends('local', 'product_qty')
    def _compute_local_cant(self):
        for line in self:
            if line.local <= 0 or line.local <= 0:
                line.local_cant = 0.0
            else:
                line.local_cant = math.ceil(line.local * line.product_qty)

    @api.depends('cost_custom', 'destination_expenses', 'logistic_margin')
    def _compute_local_incoterm(self):
        for line in self:
            line.local_incoterm = math.ceil(line.cost_custom + line.destination_expenses + line.logistic_margin)

    @api.depends('local_incoterm', 'local_cant')
    def _compute_total_customer(self):
        for line in self:
            line.total_customer = math.ceil(line.local_incoterm + line.local_cant)

    @api.depends('total_customer', 'product_qty')
    def _compute_DDP_unit(self):
        for line in self:
            if line.total_customer <= 0 or line.total_customer <= 0 or line.product_qty <= 0:
                line.DDP_unit = 0.0
            else:
                line.DDP_unit = math.ceil(line.total_customer / line.product_qty)
    
    @api.depends('DDP_unit', 'product_qty')
    def _compute_DDP_total(self):
        for line in self:
            if line.DDP_unit <= 0 or line.DDP_unit <= 0:
                line.DDP_total = 0.0
            else:
                line.DDP_total = math.ceil(line.DDP_unit * line.product_qty)

    @api.depends('local_utility', 'utility', 'local_buy', 'is_first_product')
    def _compute_utility_cac(self):
        for line in self:
            _logger.info(f"Producto {line.id}: is_first_product = {line.is_first_product}")
            # Solo se ejecutará para el primer producto
            if line.is_first_product:
                # Comprobar si utility y local_utility están disponibles
                if line.utility <= 0 or line.local_utility <= 0:
                    line.utility_cac = 0.0
                else:
                    # Calcular el valor utilizando la lógica de la fórmula
                    utility_difference = line.utility - line.local_utility
                    local_utility_sum = sum(l.utility_cac for l in line.ipbu_id.product_line_ids if l.local_buy == 'yes')
                    line.utility_cac = math.ceil(utility_difference + local_utility_sum)
            else:
                line.utility_cac = math.ceil(line.utility - line.local_utility)

    @api.depends('cost', 'utility_cac', 'product_qty')
    def _compute_cac(self):
        for line in self:
            if line.product_qty <= 0:
                line.cac = 0.0
            else:
                line.cac = math.ceil((line.cost + line.utility_cac) / line.product_qty)

    @api.depends('cac', 'product_qty')
    def _compute_cac_cant(self):
        for line in self:
            if line.product_qty <= 0:
                line.cac_cant = 0.0
            else:
                line.cac_cant = math.ceil(line.cac * line.product_qty)
    
    @api.depends('origin_expenses')
    def _compute_incoterm_cac(self):
        for line in self:
            line.incoterm_cac = math.ceil(line.origin_expenses)

    @api.depends('cac_cant', 'incoterm_cac')
    def _compute_intern_price(self):
        for line in self:
            line.intern_price = math.ceil(line.cac_cant + line.incoterm_cac)

    @api.depends('ponderado_incoterm')
    def _compute_origin_expenses(self):
        for line in self:
            if line.ipbu_id.category == 'Repuestos':
                line.origin_expenses = line.ipbu_id.total_origin_expenses * line.ponderado_incoterm

    @api.depends('ponderado_incoterm')
    def _compute_cost_custom(self):
        for line in self:
            if line.ipbu_id.category == 'Repuestos':
                line.cost_custom = line.ipbu_id.total_cost_custom * line.ponderado_incoterm

    @api.depends('ponderado_incoterm')
    def _compute_destination_expenses(self):
        for line in self:
            if line.ipbu_id.category == 'Repuestos':
                line.destination_expenses = line.ipbu_id.total_destination_expenses * line.ponderado_incoterm

    @api.depends('product_id')
    def _compute_description(self):
        for line in self:
            if line.product_id:
                line.product_description = line.product_id.description_sale

    @api.depends('ipbu_id.category')
    def _compute_category(self):
        for line in self:
            line.category = line.ipbu_id.category