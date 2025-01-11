{
    "name": "IPBU",  # The name of the module.
    "version": "1.0",  # The version of the module.
    "category": "Accounting",  # This module falls under the 'Accounting' category.
    "summary": "Module for cost management",  # A brief description of what the module does.
    "description": "This module helps in managing and analyzing costs.",  # Detailed explanation of the module's purpose.
    
    # List of module dependencies: these are the Odoo modules that this module relies on.
    "depends": [
        "base",  # Odoo's base module, providing the core framework.
        "account",  # Odoo's accounting module for managing finances.
        "product",  # Odoo's product management module.
        "sale_management",  # Sales management module for handling orders and invoices.
        "crm",  # CRM (Customer Relationship Management) module for managing customer interactions.
        "sale",
        "web"
    ],
    
    # Data files to be loaded when the module is installed.
    "data": [
        "data/security.xml",  # Defines security rules for the IPBU module.
        "data/ir_sequence.xml",  # Defines sequences for generating numbers (e.g., invoice numbers).
        
        # View files for the IPBU module and CRM, Sale Order, and Ticket views for integration.
        "views/ipbu_views.xml",  # Views for cost management interfaces.
        "views/ipbu_menu.xml",  # Menu configuration to access the module's features.
        "views/crm_lead_views.xml",  # Custom views for managing CRM leads.
        "views/crm_lead_kanban.xml",  # Kanban view for visualizing CRM leads.
        "views/sale_order.xml",  # Views for managing sale orders with cost information.
        "views/sale_order_kanban.xml",  # Kanban-style view for managing sale orders.
        "views/crm_quick_create.xml",
        "views/sale_order_incoterm.xml",
        'views/sale_order_stock_inherit.xml',
        'report/custom_quotation_report.xml',
        'report/custom_quotation_template.xml'
    ],
    
    # The following configurations:
    "installable": True,  # Specifies that the module can be installed.
    "application": False,  # This is not a standalone application; it integrates with existing Odoo features.
    
    'license': "LGPL-3",  # The license under which the module is distributed (Lesser General Public License 3).
}
