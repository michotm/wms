# Copyright 2020 Akretion (https://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, fields
from odoo.osv import expression

from odoo.addons.base_rest.components.service import to_bool, to_int
from odoo.addons.component.core import Component

from .service import to_float


class Inventory(Component):
    """
    Inventory

    1) create an inventory in odoo
    2) pick one in mobile app
    3) if sub locations, ask to choose a location
    4) scan a product or a pack or number of lot
    5) scan again the same to increase qty (local)
    6) scan something else to trigger the sent

    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.inventory"
    _usage = "inventory"
    _description = __doc__

    def _response_for_manual_selection(self, inventories, message=None):
        data = {
            "records": self.data.inventories(inventories),
            "size": len(inventories),
        }
        return self._response(next_state="manual_selection", data=data, message=message)

    def _response_for_scan_location(self, inventory, message=None):
        data = self.data.inventory(inventory)
        return self._response(next_state="scan_location", data=data, message=message)

    def _response_for_scan_product(self, inventory, location, message=None):
        data = {
            "inventory": self.data.inventory(inventory),
            "location": self.data.location(location),
        }
        return self._response(next_state="scan_product", data=data, message=message)

    def list_inventories(self):
        inventories = self._inventory_search()
        return self._response_for_manual_selection(inventories)

    def select_inventory(self, inventory_id):
        """ Get informations about an inventory"""
        # products
        # locations
        # params
        inventory = self._inventory_search(inventory_ids=[inventory_id])
        if inventory:
            return self._response_for_scan_location(inventory)
        else:
            return self._response(
                base_response=self.list_inventories(),
                message={
                    "message_type": "warning",
                    "body": _("This inventory cannot be selected."),
                })

    def _inventory_base_search_domain(self):
        return [('state', 'in', ('draft', 'confirm'))]

    def _inventory_search(self, inventory_ids=None):
        domain = self._inventory_base_search_domain()
        if inventory_ids:
            domain = expression.AND([domain, [("id", "in", inventory_ids)]])
        return self.env['stock.inventory'].search(domain)

    def scan_location(self, inventory_id, barcode):
        """Scan a location
        """
        inventory = self._inventory_search(inventory_ids=[inventory_id])
        search = self.actions_for("search")
        location = search.location_from_scan(barcode)
        if not location:
            return self._response_for_start_line(
                inventory, message=self.msg_store.barcode_not_found()
            )
        if not location.is_sublocation_of(inventory.location_ids):
            return self._response_for_start_line(
                inventory, message={
                    "message_type": "warning",
                    "body": _("This location is not tied to the current inventory adjustement"),
                }
            )
        return self._response_for_scan_product(inventory, location)

        def select_location(self, inventory_id, location_id):
        """ refactorer: scan_location, dès que le barcode trouve
        la location, il devrait appeler select_location"""
          pass

    def scan_something(self, inventory_id=None, location_id=None, barcode=None):
        search = self.actions_for("search")
        if not inventory_id:
            # we assume barcode is an inventory? 
            return  # not implemented
        inventory = self._inventory_search(inventory_ids=[inventory_id])
        if not inventory:
            # return error msg
            return
        if not location_id:
            # we assume barcode is a location_id
            location_id = search.location_from_scan(barcode)
            if not location_id:
                # return error msg
                return
        location = self._location_search(inventory, location_ids=[location_id])

        # barcode now can be a pack, a lot or a product, or something exotic (like
        # a lot+product+weight?
        # pack and lot to be implemented 
        search.product_from_scan(barcode)
        return


    def scan_product(self, inventory_id, location_id, barcode, qty, confirm):
        # refactorer la recherche et validation du couple
        # inventory_id / location_id
        inventory = self.env['stock.inventory'].browse(inventory_id)
        location = self.env['stock.location'].browse(location_id)
        search = self.actions_for("search")
        product = search.product_from_scan(barcode)
        if not product:
            # todo manage new products
            return self._response_for_scan_product(
                inventory, location, message=self.msg_store.barcode_not_found()
            )

        # find inventory_line for this product
        lines = inventory.lines.filtered(lambda l: l.product_id == product.id)
        if not lines:
            # todo manage not in inventory lines
            return
        if len(lines) > 1:
            # todo manage lots or something else
            return
        if lines.product_qty != 0.0: # todo float compare
            # ask ocnfirmation,
            if not confirm:
                return with_confirmation
            if confirm == 'replace':
                # do nothing
                qty_to_set = qty
            elif confirm == 'add':
                qty_to_set = qty + lines.product_qty
        else:
            qty_to_set = qty
        lines.product_qty = qty_to_set
        return self._response_for_scan_product(
            inventroy, location)
        # TODO : trouver un moyen de dire que c'était good



class ShopfloorInventoryValidator(Component):
    """Validators for the Cluster Picking endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.inventory.validator"
    _usage = "inventory.validator"


    def list_inventories(self):
        return {}

    def select_inventory(self):
        return {
            "inventory_id": {"coerce": to_int, "required": True, "type": "integer"}
        }

    def scan_location(self):
        return {
            "inventory_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }


class ShopfloorInventoryValidatorResponse(Component):
    """Validators for the Cluster Picking endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.inventory.validator.response"
    _usage = "inventory.validator.response"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "start": self._schema_for_select_inventory,
            "manual_selection": self._schema_for_inventory_selection,
            "scan_location": self._schema_for_scan_location,
            "scan_product": self._schema_for_scan_product,
        }

    def list_inventories(self):
        return self._response_schema(next_states={"manual_selection"})

    def select_inventory(self):
        return self._response_schema(next_states={"manual_selection", "scan_location"})

    def select_location(self):
        return self._response_schema(next_states={"scan_product"})

    @property
    def _schema_for_select_inventory(self):
        schema = self.schemas.inventory()
        #schema["lines"] = self.schemas._schema_dict_of(self.schemas.inventory_line())
        return schema

    @property
    def _schema_for_inventory_selection(self):
        return self.schemas._schema_search_results_of(self.schemas.inventory())

    @property
    def _schema_for_scan_product(self):
        return self.schemas.inventory_location()

    @property
    def _schema_for_scan_location(self):
        return self.schemas.inventory()
