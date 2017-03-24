# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.pool import Pool
from .purchase import *
from .product import *
from .stock import *

def register():
    Pool.register(
        Purchase,
        Template,
        MoveProductStockStart,
        PrintReportTransferStart,
        module='nodux_purchase_product_stock_one', type_='model')
    Pool.register(
        WizardPurchasePayment,
        MoveProductStock,
        PrintReportTransfer,
        module='nodux_purchase_product_stock_one', type_='wizard')
    Pool.register(
        ReportTransfer,
        module='nodux_purchase_product_stock_one', type_='report')
