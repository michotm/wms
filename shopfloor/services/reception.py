# Copyright 2020 Akretion (https://akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import pdb
from odoo import _

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from .service import to_float

from .exception import (
    response_decorator
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

    def _search_picking_by_partner_id(self, id):
        return [
            ("state", "=", "assigned"),
            ("picking_type_id", "in", self.picking_types.ids),
            ("partner_id", "=", id),
        ]

    def _lines_checkout_done(self, picking):
        return picking.move_line_ids.filtered(self._filter_lines_checkout_done)

    def _lines_to_receive(self, picking):
        return picking.move_line_ids.filtered(self._filter_lines_to_receive)

    def _order_for_list_stock_picking(self):
        return "scheduled_date asc, id asc"

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


    def _response_for_manual_selection(self, message=None):
        pickings = self.env["stock.picking"].search(
            self._domain_for_list_stock_picking(),
            order=self._order_for_list_stock_picking(),
        )
        data = {"pickings": self.data.pickings(pickings)}
        return self._response(next_state="manual_selection", data=data, message=message)

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

    @response_decorator
    def list_vendor_with_pickings(self):
        return self._response_for_start()

    @response_decorator
    def list_stock_picking(self):
        """List stock.picking records available

        Returns a list of all the available records for the current picking
        type.

        Transitions:
        * manual_selection: to the selection screen
        """
        return self._response_for_manual_selection()

    @response_decorator
    def select_line(self, picking_id, package_id=None, move_line_id=None):
        """Select move lines of the stock picking

        This is the same as ``scan_line``, except that a package id or a
        move_line_id is given by the client (user clicked on a list).

        It returns a list of move line ids that will be displayed by the
        screen ``select_package``. This screen will have to send this list to
        the endpoints it calls, so we can select/deselect lines but still
        show them in the list of the client application.

        Transitions:
        * select_line: nothing could be found for the barcode
        * select_package: lines are selected, user is redirected to this
        screen to change the qty done and destination package if needed
        """
        assert package_id or move_line_id

        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)

        selection_lines = self._lines_to_receive(picking)
        if not selection_lines:
            return self._response_for_summary(picking)

        if package_id:
            package = self.env["stock.quant.package"].browse(package_id).exists()
            return self._select_line_package(picking, selection_lines, package)
        if move_line_id:
            move_line = self.env["stock.move.line"].browse(move_line_id).exists()
            return self._select_line_move_line(picking, selection_lines, move_line)


class ShopfloorReceptionValidator(Component):
    """Validators for the Checkout endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.reception.validator"
    _usage = "reception.validator"

    def list_vendor_with_pickings(self):
        return {}

    def list_stock_picking(self):
        return {"partner_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def select(self):
        return {"picking_id": {"coerce": to_int, "required": True, "type": "integer"}}


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
        }

    def list_vendor_with_pickings(self):
        return self._response_schema(next_states={"start"})

    def list_stock_picking(self):
        return self._response_schema(next_states={"manual_selection"})

    def select(self):
        return self._response_schema(
            next_states={"manual_selection", "summary", "select_line"}
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
