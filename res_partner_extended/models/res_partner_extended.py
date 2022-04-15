# -*- coding: utf-8 -*-

from odoo import api, models, fields
import logging


_logger = logging.getLogger(__name__)


class ResPartnerExtended(models.Model):
    _inherit = 'res.partner'    
    

    @api.model
    def _compute_display_name(self):
        diff = dict(show_address=None, show_address_only=None, show_email=None, html_format=None, show_vat=None)
        names = dict(self.with_context(**diff).name_get())
        for partner in self:
            partner.display_name = names.get(partner.id)  
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

    def name_get(self):
        """ Return the categories' display name, including their direct
            parent by default.
            If ``context['partner_category_display']`` is ``'short'``, the short
            version of the category name (without the direct parent) is used.
            The default is the long version.
        """
        if self._context.get('default_type') == 'delivery':
            res = []
            for category in self:
                res.append( (category.id, category.display_name) )
            return res  
        if self._context.get('partner_category_display') == 'short':
            return super(PartnerCategory, self).name_get()

        res = []
        for category in self:
            names = []
            current = category
            while current:
                names.append(current.name)
                current = current.parent_id
            res.append( (category.id, ' / '.join(reversed(names))) )
        return res  