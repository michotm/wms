# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, fields

from odoo.addons.component.core import Component

class InputStockTransfer(Component):
    """
    Methods for Input Stock Transfer Process

    Allows the transfer of products in input location and input sublocation to their proper stock location
    This is the 2nd step in 2-step reception.

    Expected:

    * Input sublocation/Input location scanned once
    * User should be led on an optimal path through the warehouse
    * Destination scanned after each product placement on a stock location
    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.input.stock.transfer"
    _usage = "input_stock_transfer"
    _description = __doc__

    def list_input_location(self):
        #self.env["stock.picking.location"].browse(
        pass

    def scan_location(self, barcode):
        pass

class ShopfloorInputStockTransferValidator(Component):
    """Validators for the Delivery endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.input.stock.transfer.validator"
    _usage = "input_stock_transfer.validator"

    def list_input_location(self):
        return {}

    def scan_location(self):
        return {"barcode": {"required": True, "type": "string"}}


class ShopfloorInputStockTransferValidatorResponse(Component):
    """Validators for the Delivery endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.input.stock.transfer.validator.response"
    _usage = "input_stock_transfer.validator.response"

    _start_state = "start"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "start": self._schema_input_locations,
            "scan_products": self._schema_move_lines,
        }

    @property
    def _schema_input_locations(self):
        return {
            "input_locations": self.schemas._schema_list_of(
                self.schemas.location()
            ),
        }

    @property
    def _schema_move_lines(self):
        return {
            "move_lines": self.schemas._schema_list_of(
                self.schemas.move_line(with_packaging=True, with_picking=True)
            ),
            "id": {"required": True, "type": "integer"},
        }

    def list_input_location(self):
        return self._response_schema(
            next_states={"start"},
        )

    def scan_location(self):
        return self._response_schema(
            next_states={"start", "scan_products"}
        )

