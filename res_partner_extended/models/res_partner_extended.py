# -*- coding: utf-8 -*-

from odoo import api, models, fields


class ResPartnerExtended(models.Model):
    _inherit = 'res.partner'    
    

    @api.model
    def _compute_display_name(self):
        diff = dict(show_address=None, show_address_only=None, show_email=None, html_format=None, show_vat=None)
        names = dict(self.with_context(**diff).name_get())
        for partner in self:
            if partner.type == 'delivery':
                if partner.parent_id.parent_id:
                    parent = ""
                    child = ""
                    if partner.parent_id.name:
                        parent = partner.parent_id.name + ", "
                    if partner.name:
                        child = partner.name
                    partner.display_name = parent + child
                else:
                    partner.display_name = partner.name    
            else:
                partner.display_name = names.get(partner.id)  

          