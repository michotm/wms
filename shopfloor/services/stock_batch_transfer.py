# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, fields

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from .exception import (
    LocationNotFound,
    BarcodeNotFoundError,
    DestLocationNotAllowed,
    response_decorator,
)

class StockBatchTransfer(Component):
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
    _name = "shopfloor.stock.batch.transfer"
    _usage = "stock_batch_transfer"
    _description = __doc__

    def _location_search_domain(self):
        return [
            ('shopfloor_is_input_location', '=', True)
        ]

    def _move_lines_search_domain(self, location_id):
        return [
            ("picking_id.picking_type_id", "in", self.picking_types.ids),
            ("picking_id.state", "=", "assigned"),
            ("location_id.id", "=", location_id),
        ]

    def _move_lines_product_search_domain(self, location_id, product_barcode):
        return [
            ("picking_id.picking_type_id", "in", self.picking_types.ids),
            ("picking_id.state", "=", "assigned"),
            ("location_id.id", "=", location_id),
            ("product_id.barcode", "=", product_barcode),
        ]

    def list_input_location(self):
        domain = self._location_search_domain()
        records = self.env["stock.location"].search(domain)
        data = self.data_detail.locations_detail(records)
        return self._response(
            next_state="start",
            data={
                "input_locations": data,
            }
        )

    def scan_location(self, barcode):
        search = self._actions_for("search")
        location = search.location_from_scan(barcode)

        move_lines_children = self.env["stock.move.line"].search(self._move_lines_search_domain(location.id))

        return self._response(
            next_state="scan_products",
            data={
                "move_lines": self.data.move_lines(move_lines_children, with_picking=True),
                "id": location.id,
            },
            message={
                "message_type": "success",
                "body": _("{} location selected".format(location.display_name))
            }
        )

    @response_decorator
    def set_current_location(self, barcode, current_source_location_id):
        search = self._actions_for("search")
        location = search.location_from_scan(barcode)
        current_source_location = self.env["stock.location"].browse(current_source_location_id)

        move_lines_children = self.env["stock.move.line"].search(self._move_lines_search_domain(current_source_location.id))

        #We check if the current location is a destination location of at least one of the move
        #of the current_source_location
        valid_location = False
        for line in move_lines_children:
            if line.location_dest_id.id == location.id:
                valid_location = True
                break

        #If it's not we tell the user that he can't chose this destination
        if not valid_location:
            raise DestLocationNotAllowed(
                state="scan_products",
                data={
                    "move_lines": self.data.move_lines(move_lines_children, with_picking=True),
                    "id": current_source_location.id,
                }
            )

        return self._response(
            next_state="scan_products",
            data={
                "move_lines": self.data.move_lines(move_lines_children, with_picking=True),
                "id": current_source_location.id,
                "selected_location": location.id,
            },
        )

    @response_decorator
    def drop_product_to_location(self, barcode, current_source_location_id, dest_location_id):
        dest_location = self.env["stock.location"].browse(dest_location_id)
        current_source_location = self.env["stock.location"].browse(current_source_location_id)
        move_lines_children = self.env["stock.move.line"].search(self._move_lines_search_domain(current_source_location.id))
        product_move_lines = self.env["stock.move.line"].search(
            self._move_lines_product_search_domain(
                current_source_location.id,
                barcode,
            )
        )

        if not dest_location or not current_source_location:
            raise LocationNotFound(
                state="scan_products",
                data={
                    "move_lines": self.data.move_lines(move_lines_children, with_picking=True),
                    "id": current_source_location.id,
                    "selected_location": dest_location_id,
                }
            )

        if len(product_move_lines) is 0:
            raise BarcodeNotFoundError(
                state="scan_products",
                data={
                    "move_lines": self.data.move_lines(move_lines_children, with_picking=True),
                    "id": current_source_location.id,
                    "selected_location": dest_location_id,
                }
            )

        product_move_lines[0].qty_done += 1

        return self._response(
            next_state="scan_products",
            data={
                "move_lines": self.data.move_lines(move_lines_children, with_picking=True),
                "id": current_source_location.id,
                "selected_location": dest_location_id,
                "selected_product": barcode,
            },
        )



class ShopfloorStockBatchTransferValidator(Component):
    """Validators for the Delivery endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.stock.batch.transfer.validator"
    _usage = "stock_batch_transfer.validator"

    def list_input_location(self):
        return {}

    def scan_location(self):
        return {"barcode": {"required": True, "type": "string"}}

    def set_current_location(self):
        return {
            "barcode": {"required": True, "type": "string"},
            "current_source_location_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def drop_product_to_location(self):
        return {
            "barcode": {"required": True, "type": "string"},
            "current_source_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "dest_location_id": {"coerce": to_int, "required": True, "type": "integer"},
        }


class ShopfloorStockBatchTransferValidatorResponse(Component):
    """Validators for the Delivery endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.stock.batch.transfer.validator.response"
    _usage = "stock_batch_transfer.validator.response"

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
                self.schemas_detail.location_detail()
            ),
        }

    @property
    def _schema_move_lines(self):
        return {
            "move_lines": self.schemas._schema_list_of(
                self.schemas.move_line(with_packaging=True, with_picking=True)
            ),
            "id": {"required": True, "type": "integer"},
            "selected_location": {"required": False, "type": "integer"},
            "selected_product": {"required": False, "type": "string"},
        }

    def list_input_location(self):
        return self._response_schema(
            next_states={"start"},
        )

    def scan_location(self):
        return self._response_schema(
            next_states={"start", "scan_products"}
        )

    def set_current_location(self):
        return self._response_schema(
            next_states={"scan_products"}
        )

    def drop_product_to_location(self):
        return self._response_schema(
            next_states={"scan_products"}
        )
