import datetime

from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond import backend
from decimal import Decimal
from trytond.config import config
from trytond.model import ModelView, ModelSQL, fields, Unique
from trytond.pyson import Bool, Eval, Not, If, PYSONEncoder, Id
from trytond.wizard import (Wizard, StateView, StateAction, StateTransition,
    Button)


__all__ = ['Template', 'MoveProductStockStart', 'MoveProductStock']
__metaclass__ = PoolMeta


class Template:
    __name__ = 'product.template'

    total_warehouse = fields.Property(fields.Numeric('Total Products Warehouse',
        readonly=True, digits=(16, 8)))
    transferidos = fields.Property(fields.Numeric('Total Transferidos',
        readonly=True, digits=(16, 8)))

class MoveProductStockStart(ModelView):
    'Move Product Stock Start'
    __name__ = 'move_product_stock.start'

    total = fields.Property(fields.Numeric('Total Products',
        help="Total Products Move", digits=(16, 8)))

class MoveProductStock(Wizard):
    'Move Product Stock'
    __name__ = 'move_product_stock'
    #crear referencias:
    start = StateView('move_product_stock.start',
        'nodux_purchase_product_stock_one.move_product_stock_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Move', 'move_', 'tryton-ok', default=True),
            ])
    move_ = StateTransition()

    @classmethod
    def __setup__(cls):
        super(MoveProductStock, cls).__setup__()

    def default_start(self, fields):
        def in_group():
            origin = str(self)
            pool = Pool()
            ModelData = pool.get('ir.model.data')
            User = pool.get('res.user')
            Group = pool.get('res.group')
            Module = pool.get('ir.module')
            group = Group(ModelData.get_id('nodux_purchase_product_stock_one',
                            'group_trans_product'))
            transaction = Transaction()
            user_id = transaction.user
            if user_id == 0:
                user_id = transaction.context.get('user', user_id)
            if user_id == 0:
                return True
            user = User(user_id)
            return origin and group in user.groups
        if not in_group():
            self.raise_user_error('No tiene permisos para transferir productos')

        return {
            'total': Decimal(0.0),
            }

    def transition_move_(self):
        pool = Pool()
        Product = pool.get('product.template')
        products = Product.browse(Transaction().context['active_ids'])

        form = self.start

        for product in products:
            if product.type == "goods":
                if product.total_warehouse != None:
                    if product.total_warehouse >= Decimal(form.total):
                        if product.total == None:
                            if product.transferidos == None:
                                product.total = Decimal(form.total)
                                product.transferidos = Decimal(form.total)
                            else:
                                product.total = Decimal(form.total)
                                product.transferidos = product.transferidos + Decimal(form.total)
                        else:
                            if product.transferidos == None:
                                product.total = Decimal(product.total) + Decimal(form.total)
                                product.transferidos = Decimal(form.total)
                            else:
                                product.total = Decimal(product.total) + Decimal(form.total)
                                product.transferidos = product.transferidos + Decimal(form.total)

                        product.total_warehouse = product.total_warehouse - Decimal(form.total)
                        product.save()
                    else:
                        self.raise_user_error('La cantidad disponible en bodega es %s', product.total_warehouse)
                else:
                    self.raise_user_error('No existe stock disponible en Bodega')
            return 'end'
