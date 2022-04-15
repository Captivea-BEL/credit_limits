# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mashood K.U (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################

from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError
import datetime as dtt
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    warning_stage = fields.Float(string='Warning Amount',
                                 help="A warning message will appear once the selected customer is crossed warning amount."
                                      "Set its value to 0.00 to disable this feature")
    blocking_stage = fields.Float(string='Blocking Amount',
                                  help="Cannot make sales once the selected customer is crossed blocking amount."
                                       "Set its value to 0.00 to disable this feature")
    due_amount = fields.Float(string="Total Sale", compute="compute_due_amount")
    active_limit = fields.Boolean("Active Credit Limit", default=False)
    late_payment = fields.Boolean(string="Slow Pay", compute="compute_late_pay")
    
    def compute_late_pay(self):
        for rec in self:
            invoices = self.env['account.move'].search([
                    ('partner_id','=',rec.id),
                    ('invoice_payment_state', 'not in', ['paid', 'in_payment']),
                    ('type', '=', 'out_invoice'),
                    ('invoice_date_due', '<', dtt.datetime.now())
                ])
            if invoices:
                rec.late_payment = True
            else:
                rec.late_payment = False

    def compute_due_amount(self):
        for rec in self:
            if not rec.id:
                continue
            credit_amount = rec.credit
            rec.due_amount = credit_amount

    @api.constrains('warning_stage', 'blocking_stage')
    def constrains_warning_stage(self):
        if self.active_limit:
            if self.warning_stage >= self.blocking_stage:
                if self.blocking_stage > 0:
                    raise UserError(_("Warning amount should be less than Blocking amount"))


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    has_due = fields.Boolean(compute="compute_has_due")
    is_warning = fields.Boolean(compute="compute_is_warn_amount")
    due_amount = fields.Float(related='partner_id.due_amount')
    blocking_stage = fields.Float(related='partner_id.blocking_stage')
    active_limit = fields.Boolean(string="Credit Limit", related='partner_id.active_limit')
    late_payment = fields.Boolean(string="Slow Pay", related='partner_id.late_payment')


    def _action_confirm(self):
        
        """To check the selected customers due amount is exceed than blocking stage"""
        if self.partner_id.active_limit:
            #handle credit limit exceeded
            if self.due_amount + self.amount_total >= self.partner_id.blocking_stage:
                if self.partner_id.blocking_stage != 0:
                    user = self.env['res.users'].search([('id','=',self.env.uid)])
                    if user.credit_limit_override == False:
                        raise UserError("This order exceeds the customer credit limit and can not be processed with this user's authorization level")
            #Handle past due invoices
            if self.late_payment and self.active_limit:
                user = self.env['res.users'].search([('id','=',self.env.uid)])
                if user.credit_limit_override == False:
                    raise UserError("This customer credit has outstanding invoices past their terms date. This sales order can not be confirmed with this user's authorization level")
        return super(SaleOrder, self)._action_confirm()
            
    @api.depends('partner_id')
    def compute_has_due(self):
        if self.partner_id and self.due_amount > 0 :
            self.has_due = True
        else:
            self.has_due = False
            
    @api.depends('partner_id', 'amount_total')
    def compute_is_warn_amount(self):
        if self.partner_id and self.partner_id.active_limit:
            self.is_warning = False
            _logger.info(str(self.due_amount + self.amount_total) + " " + str(self.partner_id.warning_stage) ) 
            if self.due_amount + self.amount_total >= self.partner_id.warning_stage:
                if self.partner_id.warning_stage != 0:
                    self.is_warning = True
        else:
            self.is_warning = False


class User(models.Model):
    _inherit = 'res.users'

    credit_limit_override = fields.Boolean(string='Credit Limit Override', help="Allows this user to confirm Sales Orders even if the credit limit is exceeded")

