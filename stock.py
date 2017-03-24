#! -*- coding: utf8 -*-

from decimal import Decimal
from datetime import datetime
from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction
from trytond.pyson import Bool, Eval, Not, If, PYSONEncoder, Id
from trytond.wizard import (Wizard, StateView, StateAction, StateTransition,
    Button)
from trytond.modules.company import CompanyReport
from trytond.pyson import If, Eval, Bool, PYSONEncoder, Id
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.report import Report
conversor = None
try:
    from numword import numword_es
    conversor = numword_es.NumWordES()
except:
    print("Warning: Does not possible import numword module!")
    print("Please install it...!")
import pytz
from datetime import datetime,timedelta
import time


__all__ = ['PrintReportTransferStart', 'PrintReportTransfer','ReportTransfer']

_ZERO = Decimal(0)

class PrintReportTransferStart(ModelView):
    'Print Report Transfer Start'
    __name__ = 'print_report_transfer.start'

    company = fields.Many2One('company.company', 'Company', required=True)
    all_products = fields.Boolean("All products")
    product = fields.Many2One("product.template","Product", states={
        'readonly' : Eval('all_products', True),
    })
    date = fields.Date('Date', required=True)
    date_end = fields.Date('Date End', required=True)

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_all_products():
        return True

    @staticmethod
    def default_date():
        date = Pool().get('ir.date')
        return date.today()

    @staticmethod
    def default_date_end():
        date = Pool().get('ir.date')
        return date.today()

    @fields.depends('all_products', 'product')
    def on_change_all_products(self):
        if self.all_products == True:
            self.product = None

    @fields.depends('all_products', 'product')
    def on_change_product(self):
        if self.product:
            self.all_products = False


class PrintReportTransfer(Wizard):
    'Print Report Transfer '
    __name__ = 'print_report_transfer'
    start = StateView('print_report_transfer.start',
        'nodux_purchase_product_stock_one.print_transfer_report_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Print', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateAction('nodux_purchase_product_stock_one.report_transfer')

    def do_print_(self, action):
        if self.start.product:
            data = {
                'company': self.start.company.id,
                'all_products' : self.start.all_products,
                'product' : self.start.product.id,
                'date' : self.start.date,
                'date_end': self.start.date_end,
                }
        else:
            data = {
                'company': self.start.company.id,
                'all_products' : self.start.all_products,
                'product' : None,
                'date' : self.start.date,
                'date_end': self.start.date_end,
                }
        return action, data

    def transition_print_(self):
        return 'end'

class ReportTransfer(Report):
    __name__ = 'report_transfer'

    @classmethod
    def __setup__(cls):
        super(ReportTransfer, cls).__setup__()

    @classmethod
    def get_context(cls, records, data):
        pool = Pool()
        User = pool.get('res.user')
        user = User(Transaction().user)
        Date = pool.get('ir.date')
        Company = pool.get('company.company')
        Product = pool.get('product.template')
        Purchase = pool.get('purchase.purchase')
        Sale = pool.get('sale.sale')
        company = Company(data['company'])
        all_products = data['all_products']
        product_data = data['product']
        date = data['date']
        date_end = data['date_end']
        purchases = Purchase.search([('purchase_date', '>=', date), ('purchase_date', '<=', date_end)])
        sales = Sale.search([('sale_date', '>=', date), ('sale_date', '<=', date_end)])

        products_all = []

        if all_products == True:
            products = Product.search([('id','>', 0)])
            for product in products:
                product_line = {}
                comprados = Decimal(0.0)
                vendidos = Decimal(0.0)
                transferidos = Decimal (0.0)

                for purchase in purchases:
                    for line in purchase.lines:
                        if line.product.template.id == product.id:
                            comprados += Decimal(line.quantity)
                for sale in sales:
                    for line in sale.lines:
                        if line.product.template.id == product.id:
                            vendidos += Decimal(line.quantity)

                product_line['code1'] = product.code1
                product_line['name'] = product.name
                product_line['total_warehouse'] = product.total_warehouse
                product_line['total'] = product.total
                product_line['comprados'] = comprados
                product_line['vendidos'] = vendidos
                product_line['transferidos'] = comprados - product.total_warehouse
                products_all.append(product_line)

        else:
            products = Product.search([('id', '=', product_data)])
            for product in products:
                product_line = {}
                comprados = Decimal(0.0)
                vendidos = Decimal(0.0)
                transferidos = Decimal (0.0)

                for purchase in purchases:
                    for line in purchase.lines:
                        if line.product.template.id == product.id:
                            comprados += Decimal(line.quantity)
                for sale in sales:
                    for line in sale.lines:
                        if line.product.template.id == product.id:
                            vendidos += Decimal(line.quantity)

                product_line['code1'] = product.code1
                product_line['name'] = product.name
                product_line['total_warehouse'] = product.total_warehouse
                product_line['total'] = product.total
                product_line['comprados'] = comprados
                product_line['vendidos'] = vendidos
                product_line['transferidos'] = comprados - product.total_warehouse
                products_all.append(product_line)

        if company.timezone:
            timezone = pytz.timezone(company.timezone)
            dt = datetime.now()
            hora = datetime.astimezone(dt.replace(tzinfo=pytz.utc), timezone)
        else:
            company.raise_user_error('Configure la zona Horaria de la empresa')

        report_context = super(ReportTransfer, cls).get_context(records, data)

        report_context['company'] = company
        report_context['hora'] = hora.strftime('%H:%M:%S')
        report_context['fecha_im'] = hora.strftime('%d/%m/%Y')
        report_context['fecha'] = date.strftime('%d/%m/%Y')
        report_context['fecha_fin'] = date_end.strftime('%d/%m/%Y')
        report_context['products_all'] = products_all
        return report_context
