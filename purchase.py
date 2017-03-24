#! -*- coding: utf8 -*-

# This file is part of purchase_pos module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
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

__all__ = ['Purchase', 'WizardPurchasePayment']
__metaclass__ = PoolMeta


class Purchase():
    'Purchase'
    __name__ = 'purchase.purchase'

    @classmethod
    @ModelView.button
    @Workflow.transition('anulled')
    def anull(cls, purchases):
        for purchase in purchases:
            cls.raise_user_warning('anull%s' % purchase.reference,
                   'Esta seguro de anular la compra: "%s"', (purchase.reference))
            for line in purchase.lines:
                product = line.product.template
                if (product.total_warehouse + product.total) < line.quantity:
                    if product.type == "goods":
                        cls.raise_user_error('No puede anular la compra, el Stock disponible es menor a la cantidad comprada')

                else:
                    if product.type == "goods":
                        product.total_warehouse = Decimal(line.product.template.total_warehouse) + Decimal(line.product.template.total)
                        product.total = Decimal(0.0)
                        product.total_warehouse = Decimal(line.product.template.total_warehouse) - Decimal(line.quantity)
                        product.save()

        cls.write([p for p in purchases], {
                'state': 'anulled',
                })

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmed')
    def confirm(cls, purchases):
        Company = Pool().get('company.company')
        company = Company(Transaction().context.get('company'))
        for purchase in purchases:

            if purchase.party.supplier == True:
                pass
            else:
                party = purchase.party
                party.supplier = True
                party.save()

            for line in purchase.lines:
                product = line.product.template
                if product.type == "goods":
                    if line.product.template.total_warehouse == None:
                        product.total_warehouse = Decimal(line.quantity)
                    else:
                        product.total_warehouse = Decimal(line.product.template.total_warehouse) + Decimal(line.quantity)
                product.cost_price = line.unit_price
                product.save()

            if not purchase.reference:
                reference = company.sequence_purchase
                company.sequence_purchase = company.sequence_purchase + 1
                company.save()

                if len(str(reference)) == 1:
                    reference_end = 'FP-00000000' + str(reference)
                elif len(str(reference)) == 2:
                    reference_end = 'FP-0000000' + str(reference)
                elif len(str(reference)) == 3:
                    reference_end = 'FP-000000' + str(reference)
                elif len(str(reference)) == 4:
                    reference_end = 'FP-00000' + str(reference)
                elif len(str(reference)) == 5:
                    reference_end = 'FP-0000' + str(reference)
                elif len(str(reference)) == 6:
                    reference_end = 'FP-000' + str(reference)
                elif len(str(reference)) == 7:
                    reference_end = 'FP-00' + str(reference)
                elif len(str(reference)) == 8:
                    reference_end = 'FP-0' + str(reference)
                elif len(str(reference)) == 9:
                    reference_end = 'FP-' + str(reference)

                purchase.reference = str(reference_end)
                purchase.state = 'confirmed'
                purchase.save()
        cls.write([p for p in purchases], {
                'state': 'confirmed',
                })


class WizardPurchasePayment(Wizard):
    'Wizard Purchase Payment'
    __name__ = 'purchase.payment'

    def transition_pay_(self):
        pool = Pool()
        Date = pool.get('ir.date')
        User = pool.get('res.user')
        Purchase = pool.get('purchase.purchase')
        Company = pool.get('company.company')
        active_id = Transaction().context.get('active_id', False)
        purchase = Purchase(active_id)
        company = Company(Transaction().context.get('company'))
        form = self.start

        if purchase.residual_amount > Decimal(0.0):
            if form.payment_amount > purchase.residual_amount:
                self.raise_user_error('No puede pagar un monto mayor al valor pendiente %s', str(purchase.residual_amount ))

        if form.payment_amount > purchase.total_amount:
            self.raise_user_error('No puede pagar un monto mayor al monto total %s', str(purchase.total_amount ))

        if purchase.party.supplier == True:
            pass
        else:
            party = purchase.party
            party.supplier = True
            party.save()

        user, = User.search([('id', '=', 1)])
        limit = user.limit_purchase

        purchases = Purchase.search_count([('state', '=', 'confirmed')])
        if purchases > limit and user.unlimited_purchase != True:
            self.raise_user_error(u'Ha excedido el límite de Compras, contacte con el Administrador de NODUX')

        if not purchase.reference:
            for line in purchase.lines:
                product = line.product.template
                if product.type == "goods":
                    if line.product.template.total_warehouse == None:
                        product.total_warehouse = line.quantity
                    else:
                        product.total_warehouse = Decimal(line.product.template.total_warehouse) + Decimal(line.quantity)
                product.cost_price = line.unit_price
                product.save()

            reference = company.sequence_purchase
            company.sequence_purchase = company.sequence_purchase + 1
            company.save()

            if len(str(reference)) == 1:
                reference_end = 'FP-00000000' + str(reference)
            elif len(str(reference)) == 2:
                reference_end = 'FP-0000000' + str(reference)
            elif len(str(reference)) == 3:
                reference_end = 'FP-000000' + str(reference)
            elif len(str(reference)) == 4:
                reference_end = 'FP-00000' + str(reference)
            elif len(str(reference)) == 5:
                reference_end = 'FP-0000' + str(reference)
            elif len(str(reference)) == 6:
                reference_end = 'FP-000' + str(reference)
            elif len(str(reference)) == 7:
                reference_end = 'FP-00' + str(reference)
            elif len(str(reference)) == 8:
                reference_end = 'FP-0' + str(reference)
            elif len(str(reference)) == 9:
                reference_end = 'FP-' + str(reference)

            purchase.reference = str(reference_end)
            purchase.save()

        if purchase.paid_amount > Decimal(0.0):
            purchase.paid_amount = purchase.paid_amount + form.payment_amount
        else:
            purchase.paid_amount = form.payment_amount

        purchase.residual_amount = purchase.total_amount - purchase.paid_amount
        purchase.description = purchase.reference
        if purchase.residual_amount == Decimal(0.0):
            purchase.state = 'done'
        else:
            purchase.state = 'confirmed'
        purchase.save()

        return 'end'
