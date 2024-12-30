from odoo import models, fields, api
from odoo.exceptions import ValidationError
import math

class IPBU(models.Model):
    _name = 'ipbu.ipbu'
    _description = 'Modelo de ipbu'
    _rec_name = 'code'

    name = fields.Text(string='Nombre del IPBU', store=True, tracking=True, required=True)
    code = fields.Char(
        string='Código de la Hoja de Costos',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('ipbu.code') or 'New'
    )
    date = fields.Date(string='Fecha', default=fields.Date.context_today, readonly=True)

    _inherit = ['mail.thread', 'mail.activity.mixin']

    lead_id = fields.Many2one('crm.lead', string='Lead/Oportunidad', tracking=True, required=True)
    product_line_ids = fields.One2many('ipbu.product.line', 'ipbu_id', string='Líneas de Producto', tracking=True)
    total_cost_cac = fields.Float(string='Costo CAC', required=False, readonly=True, store=True, compute='_compute_total_cost_cac')
    total_sale_exw = fields.Float(string='Venta EXW', required=False, readonly=True, store=True, compute='_compute_total_sale_exw')
    total_origin_expenses = fields.Float(string='Gastos origen', required=False, store=True, compute='_compute_total_origin_expenses')
    total_cost_custom = fields.Float(string='Aduana', required=False, readonly=True, store=True, compute='_compute_total_cost_custom')
    total_destination_expenses = fields.Float(string='Gastos destino', required=False, readonly=True, store=True, compute='_compute_total_destination_expenses')
    total_logistics_margin = fields.Float(string='Margen Logístico', required=False, readonly=True, store=True, compute='_compute_total_logistics_margin')
    total_ddp = fields.Float(string='Total DDP', required=False, readonly=True, store=True, compute='_compute_total_ddp')
    margin = fields.Float(string='Margen base', required=False, tracking=True)
    line_discount = fields.Float(string='Descuento Linea', required=False, tracking=True)
    local_utility = fields.Float(string='Utilidad local', required=False, tracking=True)
    invoice_cac = fields.Float(string='Factura CAC', required=False, readonly=True, store=True, compute='_compute_total_invoice_cac')
    utility_cac = fields.Float(string='Utilidad CAC', required=False, readonly=True, store=True, compute='_compute_total_utility_cac')
    category = fields.Selection([
        ('1', 'Repuestos'),
        ('2', 'Equipos'),
    ], string='Categoria', required=False, default='Equipos', tracking=True)
    companies = fields.Many2one('res.partner', string='CAC Group', tracking=True, required=True, domain=[('x_studio_cac_group', '=', True)])
    area = fields.Text(string='Area', store=True, tracking=True, compute='_compute_area')
    principal_supplier = fields.Text(string='Proveedor', store=True, tracking=True, compute='_compute_principal_supplier')
    version = fields.Integer(string='Version', required=True, readonly=False, store=True, default="0")
    invoices_company = fields.Text(string='Empresa que factura', store=True, tracking=True, compute='_compute_invoices_company')
    incoterm_lead = fields.Many2one('account.incoterms', string='Incoterm', store=True, compute='_compute_incoterm', readonly=False)
    status = fields.Selection([
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
    ], string='Estado', default='inactive')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El código de la hoja de costos debe ser único.'),
        ('name_unique', 'unique(name)', 'El nombre del IPBU debe ser único.')
    ]

    has_quotation = fields.Boolean(string='Cotización Creada', default=False, tracking=True)
    quotation_id = fields.Many2one('sale.order', string='Cotización')
    lead_code = fields.Text(string='Código Oportunidad', store=True, tracking=True, compute='_compute_lead_code')


    def action_confirm(self):
        if not self.lead_id:
            raise ValidationError("La oportunidad asignada a este IPBU no existe.")
            return

        ipbu_activo = self.search([
            ('lead_id', '=', self.lead_id.id),
            ('status', '=', 'active'),
            ('id', '!=', self.id)
        ])

        if ipbu_activo:
            raise ValidationError("Esta oportunidad ya tiene una cotización Activa, primero se debe desactivar para poder activar la actual")

        self.status = 'active'

    def action_cancel(self):
        self.status = 'inactive'

    def action_convert_to_quotation(self):
        SaleOrder = self.env['sale.order']  # Referencia al modelo sale.order
        SaleOrderLine = self.env['sale.order.line']  # Referencia al modelo sale.order.line
        
        # Creamos una nueva cotización (sale.order)
        order_vals = {
            'partner_id': self.lead_id.partner_id.id,  # Asignamos el cliente desde el lead (crm.lead)
            'date_order': fields.Date.today(),
            'origin': self.code,  # Usamos el código del IPBU como referencia
            'state': 'draft',  # Estado inicial como borrador
            'opportunity_id': self.lead_id.id,
            'code': self.name,
            'incoterm': self.incoterm_lead
        }
        sale_order = SaleOrder.create(order_vals)

        # Creamos las líneas de la cotización usando los productos del IPBU
        for product_line in self.product_line_ids:

            order_line_vals = {
                'order_id': sale_order.id,  # Asignamos la cotización creada
                'product_id': product_line.product_id.id,  # Producto de la línea del IPBU
                'product_uom_qty': product_line.product_qty,  # Cantidad del producto
                'price_unit': product_line.quotation_total,  # Precio de venta (usando EXW)
                'tax_id': [(6, 0, product_line.product_id.taxes_id.ids)],  # Impuestos del producto
            }
            SaleOrderLine.create(order_line_vals)

        self.quotation_id = sale_order
        # Hacemos un seguimiento del proceso
        self.message_post(body=f'El IPBU {self.code} ha sido convertido en la cotización {sale_order.name}.')

        self.has_quotation = True

        return {
            'type': 'ir.actions.act_window',
            'name': 'Cotización',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_id': sale_order.id,
            'target': 'current',  # Se abre en la vista actual
        }

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
        
    @api.depends('lead_id')
    def _compute_area(self):
        for record in self:
            if record.lead_id:
                record.lead_id.ensure_one()
                if record.lead_id.x_studio_area:
                    first_character = record.lead_id.x_studio_area[:1].upper()
                    record.area = first_character

    @api.depends('lead_id')
    def _compute_lead_code(self):
        for record in self:
            if record.lead_id:
                record.lead_id.ensure_one()
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
        if self.lead_id:
            self.principal_supplier = self.lead_id.x_studio_main_supplier.x_studio_abbreviation
        return 

    @api.model
    def create(self, vals):
        record = super(IPBU, self).create(vals)
        record._update_first_product_flag()
        return record

    def write(self, vals):
        result = super(IPBU, self).write(vals)
        self._update_first_product_flag()
        return result

    @api.onchange('product_line_ids')
    def _update_first_product_flag(self):
        for record in self:
            if record.product_line_ids:
                for index, line in enumerate(record.product_line_ids):
                    if index == 0:
                        can_sum = False
                        total_sum = 0
                        utility_difference = line.utility - line.local_utility

                        for i, l in enumerate(line.ipbu_id.product_line_ids):
                            if l.local_buy == 'yes': 
                                can_sum = True
                            if i != 0:
                                total_sum += l.utility_cac
                            
                        local_utility_sum = total_sum if can_sum else 0

                        line.is_first_product = True
                        line.utility_cac = math.ceil(utility_difference + local_utility_sum)
                        line.supplier = line.product_id.x_studio_product_supplier.display_name

                        if record.category != "Repuestos":
                            continue

                        if  (len(record.product_line_ids) > 1 and record.product_line_ids[index].product_cost != 0 and record.product_line_ids[index + 1].product_cost != 0):
                            total = sum(l.sale_qty_exw for l in record.product_line_ids if l.sale_qty_exw)
                            line.ponderado_incoterm = min(0.65, line.sale_qty_exw / total)
                        else:
                            line.ponderado_incoterm = 1
                    else:
                        line.is_first_product = False
                        line.utility_cac = math.ceil(line.utility - line.local_utility)
                        line.supplier = line.product_id.x_studio_product_supplier.display_name
                        
                        if record.category != "Repuestos":
                            continue

                        total = 0
                        
                        for i, l in enumerate(record.product_line_ids):
                            if(i != 0):
                                total += l.sale_qty_exw

                        if (line.sale_qty_exw != 0 and total != 0):
                            line.ponderado_incoterm = (line.sale_qty_exw / total) * (1 - record.product_line_ids[0].ponderado_incoterm)
    
    def action_view_quotation(self):
        self.ensure_one()
        if self.quotation_id:
            return {
                'name': 'Cotización',
                'domain': [('id', '=', self.quotation_id.id)],
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'context': {'default_lead_id': self.lead_id.id},
            }