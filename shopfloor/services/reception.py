# Copyright 2020 Akretion (https://akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import pdb
from odoo import _

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from .service import to_float

from .exception import (
    StockPickingNotFound,
    CannotMovePickingType,
    StockPickingNotAvailable,
    response_decorator,
)

class Reception(Component):
    """
    Methods for the Reception Process

    This scenario runs on existing moves.
    It happens on the "Packing" step of a pick/pack/ship.

    Use cases:

    1) Products are packed (e.g. full pallet shipping) and we keep the packages
    2) Products are packed (e.g. rollercage bins) and we create a new package
       with same content for shipping
    3) Products are packed (e.g. half-pallet ) and we merge several into one
    4) Products are packed (e.g. too high pallet) and we split it on several
    5) Products are not packed (e.g. raw products) and we create new packages
    6) Products are not packed (e.g. raw products) and we do not create packages

    A new flag ``shopfloor_checkout_done`` on move lines allows to track which
    lines have been checked out (can be with or without package).

    Flow Diagram: https://www.draw.io/#G1qRenBcezk50ggIazDuu2qOfkTsoIAxXP
    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.reception"
    _usage = "reception"
    _description = __doc__

    @staticmethod
    def _filter_lines_to_receive(move_line):
        return move_line.product_uom_qty != move_line.qty_done and not move_line.shopfloor_checkout_done

    def _create_data_for_scan_products(self, partner_id, move_line_ids):
        pickings = self.env["stock.picking"].search(
            self._search_picking_by_partner_id(partner_id),
            order=self._order_for_list_stock_picking(),
        )
        move_lines = pickings.mapped('move_line_ids')
        move_lines_picked = self.env["stock.move.line"].search(
            self._search_move_line_picked(partner_id),
            order=self._order_for_move_line(),
        )
        move_lines_picking = self.env["stock.move.line"].search(
            [("id", "in", move_line_ids)],
            order=self._order_for_move_line(),
        )
        move_lines_data = {
            "move_lines": self.data.move_lines(move_lines),
            "id": partner_id,
            "move_lines_picked": self.data.move_lines(move_lines_picked),
            "move_lines_picking": self.data.move_lines(move_lines_picking),
        }

        return move_lines_data

    def _data_for_move_lines(self, lines, **kw):
        return self.data.move_lines(lines, **kw)

    def _data_for_stock_picking(self, picking, done=False):
        data = self.data.picking(picking)
        line_picker = self._lines_checkout_done if done else self._lines_to_receive
        data.update(
            {
                "move_lines": self._data_for_move_lines(
                    line_picker(picking), with_packaging=done
                )
            }
        )
        return data

    def _deselect_lines(self, lines):
        lines.filtered(lambda l: not l.shopfloor_checkout_done).qty_done = 0

    def _domain_for_list_stock_picking(self):
        return [
            ("state", "=", "assigned"),
            ("picking_type_id", "in", self.picking_types.ids),
        ]

    def _search_picking_by_partner_id(self, id, state="assigned"):
        return [
            ("state", "=", state),
            ("picking_type_id", "in", self.picking_types.ids),
            ("partner_id", "=", id),
        ]

    def _search_move_line_picked(self, id):
        return [
            ("picking_id.state", "=", "assigned"),
            ("picking_id.picking_type_id", "in", self.picking_types.ids),
            ("picking_id.partner_id", "=", id),
            ("state", "=", "done"),
        ]

    def _search_move_line_by_product(self, id, barcode):
        return [
            ("picking_id.state", "=", "assigned"),
            ("picking_id.picking_type_id", "in", self.picking_types.ids),
            ("picking_id.partner_id", "=", id),
            ("product_id.barcode", "=", barcode),
            ("state", "not in", ("cancel", "done")),
        ]

    def _lines_checkout_done(self, picking):
        return picking.move_line_ids.filtered(self._filter_lines_checkout_done)

    def _lines_to_receive(self, picking):
        return picking.move_line_ids.filtered(self._filter_lines_to_receive)

    def _order_for_list_stock_picking(self):
        return "scheduled_date asc, id asc"

    def _order_for_move_line(self):
        return "date asc, id asc"

    def _response_for_scan_products(self, partner_id, move_line_ids=None, message=None):
        move_lines_data = self._create_data_for_scan_products(
            partner_id,
            move_line_ids,
        )

        return self._response(
            next_state="scan_products",
            data=move_lines_data,
            message=message,
        )

    def _response_for_start(self, message=None):
        pickings = self.env["stock.picking"].search(
            self._domain_for_list_stock_picking(),
            order=self._order_for_list_stock_picking(),
        )
        partners = pickings.mapped('partner_id')
        partners_data = self.data.partners(partners)

        for partner in partners_data:
            pickings = self.env["stock.picking"].search(
                self._search_picking_by_partner_id(partner["id"]),
            )
            partner["picking_count"] = len(pickings)

        data = {"partners": partners_data}

        return self._response(next_state="start", data=data, message=message)

    def _response_for_select_document(self, message=None):
        return self._response(next_state="select_document", message=message)

    def _response_for_select_line(self, picking, message=None):
        if all(line.shopfloor_checkout_done for line in picking.move_line_ids):
            return self._response_for_summary(picking, message=message)
        return self._response(
            next_state="select_line",
            data={"picking": self._data_for_stock_picking(picking)},
            message=message,
        )

    def _response_for_summary(self, picking, need_confirm=False, message=None):
        return self._response(
            next_state="summary" if not need_confirm else "confirm_done",
            data={
                "picking": self._data_for_stock_picking(picking, done=True),
                "all_processed": not bool(self._lines_to_receive(picking)),
            },
            message=message,
        )

    def _select_lines(self, lines):
        for line in lines:
            if line.shopfloor_checkout_done:
                continue
            line.qty_done = line.product_uom_qty

        picking = lines.mapped("picking_id")
        other_lines = picking.move_line_ids - lines
        self._deselect_lines(other_lines)

    def _select_lines_from_package(self, picking, selection_lines, package):
        lines = selection_lines.filtered(lambda l: l.package_id == package)
        if not lines:
            return self._response_for_select_line(
                picking,
                message={
                    "message_type": "error",
                    "body": _("Package {} is not in the current transfer.").format(
                        package.name
                    ),
                },
            )
        self._select_lines(lines)
        return self._response_for_select_package(picking, lines)

    def _select_line_move_line(self, picking, selection_lines, move_line):
        if not move_line:
            return self._response_for_select_line(
                picking, message=self.msg_store.record_not_found()
            )
        # normally, the client should sent only move lines out of packages, but
        # in case there is a package, handle it as a package
        if move_line.package_id:
            return self._select_lines_from_package(
                picking, selection_lines, move_line.package_id
            )
        self._select_lines(move_line)
        return self._response_for_select_package(picking, move_line)

    def _select_line_package(self, picking, selection_lines, package):
        if not package:
            return self._response_for_select_line(
                picking, message=self.msg_store.record_not_found()
            )
        return self._select_lines_from_package(picking, selection_lines, package)

    def _select_picking(self, picking, state_for_error, data):
        if not picking:
            raise StockPickingNotFound(state_for_error, data)
        if picking.picking_type_id not in self.picking_types:
            raise CannotMovePickingType(state_for_error, data)
        if picking.state != "assigned":
            raise StockPickingNotAvailable(state_for_error, data)

        return self._response_for_select_line(picking)

    @response_decorator
    def list_vendor_with_pickings(self):
        return self._response_for_start()

    @response_decorator
    def list_move_lines(self, partner_id):
        """List stock.picking records available

        Returns a list of all the available records for the current picking
        type.

        Transitions:
        * manual_selection: to the selection screen
        """
        return self._response_for_scan_products(partner_id)

    @response_decorator
    def scan_product(self, partner_id, barcode):
        product_move_lines = self.env["stock.move.line"].search(
            self._search_move_line_by_product(partner_id, barcode),
            order=self._order_for_move_line(),
        )

        product_move_lines[0].qty_done += 1

        return self._response_for_scan_products(partner_id, product_move_lines.ids)

    def increase_quantity(self, partner_id, barcode, move_lines_picking):
        print(move_lines_picking)
        return self._response_for_scan_products(partner_id, move_lines_picking)

    def set_quantity(self, partner_id, barcode, move_lines_picking, qty):
        print(move_lines_picking)

    def set_quantity(self, partner_id, barcode, qty):
        product_move_lines = self.env["stock.move_line"].search(
            self._search_move_line_by_product(partner_id, barcode),
            order=self._order_for_move_line(),
        )

class ShopfloorReceptionValidator(Component):
    """Validators for the Checkout endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.reception.validator"
    _usage = "reception.validator"

    def list_vendor_with_pickings(self):
        return {}

    def list_move_lines(self):
        return {"partner_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def scan_product(self):
        return {
            "partner_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def increase_quantity(self):
        return {
            "partner_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
            "move_lines_picking": {"required": True, "type": "list", "schema": {"coerce": to_int, "type": "integer"}},
        }

    def set_quantity(self):
        return {
            "partner_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
            "move_lines_picking": {"required": True, "type": "list", "schema": {"coerce": to_int, "type": "integer"}},
        }

class ShopfloorReceptionValidatorResponse(Component):
    """Validators for the Checkout endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.reception.validator.response"
    _usage = "reception.validator.response"

    _start_state = "start"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "manual_selection": self._schema_selection_list,
            "start": self._schema_partner_list,
            "summary": self._schema_summary,
            "scan_products": self._schema_for_move_lines_details,
        }

    def list_vendor_with_pickings(self):
        return self._response_schema(next_states={"start"})

    def list_move_lines(self):
        return self._response_schema(next_states={"scan_products"})

    def scan_product(self):
        return self._response_schema(next_states={"scan_products", "summary"})

    def increase_quantity(self):
        return self._response_schema(next_states={"scan_products", "summary"})

    def set_quantity(self):
        return self._response_schema(next_states={"scan_products", "summary"})

    def _schema_stock_picking(self, lines_with_packaging=False):
        schema = self.schemas.picking()
        schema.update(
            {
                "move_lines": self.schemas._schema_list_of(
                    self.schemas.move_line(with_packaging=lines_with_packaging)
                )
            }
        )
        return {"picking": self.schemas._schema_dict_of(schema, required=True)}

    @property
    def _schema_stock_picking_details(self):
        return self._schema_stock_picking()

    @property
    def _schema_summary(self):
        return dict(
            self._schema_stock_picking(lines_with_packaging=True),
            all_processed={"type": "boolean"},
        )

    @property
    def _schema_partner_list(self):
        return {
            "partners": self.schemas._schema_list_of(self.schemas.partner(with_picking_count=True)),
        }

    @property
    def _schema_selection_list(self):
        return {
            "pickings": self.schemas._schema_list_of(self.schemas.picking()),
        }

    @property
    def _schema_for_move_lines_details(self):
        return {
            "move_lines": self.schemas._schema_list_of(self.schemas.move_line()),
            "id": {"required": True, "type": "integer"},
            "move_lines_picked": self.schemas._schema_list_of(self.schemas.move_line()),
            "move_lines_picking": self.schemas._schema_list_of(self.schemas.move_line()),
        }
