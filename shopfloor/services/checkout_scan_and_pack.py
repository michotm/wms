# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from werkzeug.exceptions import BadRequest

from odoo import _

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class CheckoutScanAndPack(Component):
    """
    Methods for the Checkout Process

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
    _name = "shopfloor.checkout_scan_and_pack"
    _usage = "checkout_scan_and_pack"
    _description = __doc__

    def _response_for_select_line(self, picking, message=None, skip=None):
        next_state = "scan_products"

        return self._response(
            next_state=next_state,
            data={"picking": self._data_for_stock_picking(picking), "skip": skip},
            message=message,
        )

    def _response_for_summary(self, picking, need_confirm=False, message=None):
        return self._response(
            next_state="summary" if not need_confirm else "confirm_done",
            data={
                "picking": self._data_for_stock_picking(picking, done=True),
                "all_processed": not bool(self._lines_to_pack(picking)),
            },
            message=message,
        )

    def _response_for_select_document(self, message=None):
        return self._response(next_state="select_document", message=message)

    def _response_for_manual_selection(self, message=None):
        pickings = self.env["stock.picking"].search(
            self._domain_for_list_stock_picking(),
            order=self._order_for_list_stock_picking(),
        )
        data = {"pickings": self.data.pickings(pickings)}
        return self._response(next_state="manual_selection", data=data, message=message)

    def _response_for_change_packaging(self, picking, package, packaging_list):
        if not package:
            return self._response_for_summary(
                picking, message=self.msg_store.record_not_found()
            )

        return self._response(
            next_state="change_packaging",
            data={
                "picking": self.data.picking(picking),
                "package": self.data.package(
                    package, picking=picking, with_packaging=True
                ),
                "packaging": self.data.packaging_list(packaging_list.sorted()),
            },
        )

    def _select_picking(self, picking, state_for_error, skip=0):
        if not picking:
            if state_for_error == "manual_selection":
                return self._response_for_manual_selection(
                    message=self.msg_store.stock_picking_not_found()
                )
            return self._response_for_select_document(
                message=self.msg_store.barcode_not_found()
            )
        if picking.picking_type_id not in self.picking_types:
            if state_for_error == "manual_selection":
                return self._response_for_manual_selection(
                    message=self.msg_store.cannot_move_something_in_picking_type()
                )
            return self._response_for_select_document(
                message=self.msg_store.cannot_move_something_in_picking_type()
            )
        if picking.state != "assigned":
            if state_for_error == "manual_selection":
                return self._response_for_manual_selection(
                    message=self.msg_store.stock_picking_not_available(picking)
                )
            return self._response_for_select_document(
                message=self.msg_store.stock_picking_not_available(picking)
            )
        return self._response_for_select_line(picking, skip=skip)

    def _data_for_move_lines(self, lines, **kw):
        move_line = self.data.move_lines(lines, **kw)
        return move_line

    def _data_for_stock_picking(self, picking, done=False):
        data = self.data.picking(picking)
        line_picker = self._lines_checkout_done if done else self._lines_to_pack
        data.update(
            {
                "move_lines": self._data_for_move_lines(
                    line_picker(picking), with_packaging=done
                )
            }
        )
        return data

    def _lines_checkout_done(self, picking):
        return picking.move_line_ids.filtered(self._filter_lines_checkout_done)

    def _lines_to_pack(self, picking):
        # if we scan one by one we want all the lines
        return picking.move_line_ids

    def _domain_for_list_stock_picking(self):
        return [
            ("state", "=", "assigned"),
            ("picking_type_id", "in", self.picking_types.ids),
        ]

    def _order_for_list_stock_picking(self):
        return "scheduled_date asc, id asc"


    @staticmethod
    def _filter_lines_unpacked(move_line):
        return (
            move_line.qty_done == 0 or move_line.shopfloor_user_id
        ) and not move_line.shopfloor_checkout_done

    @staticmethod
    def _filter_lines_checkout_done(move_line):
        return move_line.qty_done > 0 and move_line.shopfloor_checkout_done

    def _get_allowed_packaging(self):
        return self.env["product.packaging"].search([("product_id", "=", False)])

    def scan_document(self, barcode, skip=0):
        """Scan a package, a stock.picking or a location

        When a location is scanned, if all the move lines from this destination
        are for the same stock.picking, the stock.picking is used for the
        next steps.

        When a package is scanned, if the package has a move line to move it
        from a location/sublocation of the current stock.picking.type, the
        stock.picking for the package is used for the next steps.

        When a stock.picking is scanned, it is used for the next steps.

        In every case above, the stock.picking must be entirely available and
        must match the current picking type.

        Transitions:
        * select_document: when no stock.picking could be found
        * select_line: a stock.picking is selected
        * summary: stock.picking is selected and all its lines have a
          destination pack set
        """
        search = self._actions_for("search")
        picking = search.picking_from_scan(barcode)

        if not picking:
            location = search.location_from_scan(barcode)
            if location:
                if not location.is_sublocation_of(
                    self.picking_types.mapped("default_location_src_id")
                ):
                    return self._response_for_select_document(
                        message=self.msg_store.location_not_allowed()
                    )
                lines = location.source_move_line_ids.filtered(
                    lambda ml: ml.state not in ("cancel", "done")
                )

                pickings = lines.mapped("picking_id")
                if skip >= len(pickings):
                    picking = pickings[-1]
                    return self._response_for_select_line(
                        picking,
                        message={
                            "message_type": "error",
                            "body": _("There's no more order to skip"),
                        },
                    )
                picking = pickings[skip : skip + 1]  # take the first one

        if not picking:
            package = search.package_from_scan(barcode)
            if package:
                pickings = package.move_line_ids.filtered(
                    lambda ml: ml.state not in ("cancel", "done")
                ).mapped("picking_id")
                if len(pickings) > 1:
                    # Filter only if we find several pickings to narrow the
                    # selection to one of the good type. If we have one picking
                    # of the wrong type, it will be caught in _select_picking
                    # with the proper error message.
                    # Side note: rather unlikely to have several transfers ready
                    # and moving the same things
                    pickings = pickings.filtered(
                        lambda p: p.picking_type_id in self.picking_types
                    )
                if len(pickings) == 1:
                    picking = pickings
        return self._select_picking(picking, "select_document", skip)

    def list_packaging(self, picking_id, package_id):
        """List the available package types for a package

        For a package, we can change the packaging. The available
        packaging are the ones with no product.

        Transitions:
        * change_packaging
        * summary: if the package_id no longer exists
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)
        package = self.env["stock.quant.package"].browse(package_id).exists()
        packaging_list = self._get_allowed_packaging()
        return self._response_for_change_packaging(picking, package, packaging_list)

    def set_quantity(self, picking_id, move_line_id, qty):
        picking = self.env["stock.picking"].browse(picking_id)
        move_line = self.env["stock.move.line"].browse(move_line_id)

        message = self._check_picking_status(picking)

        if message:
            return self._response_for_select_document(message=message)

        quantity_to_set = qty

        if quantity_to_set > move_line.product_uom_qty:
            return self._response_for_scanned_product(
                picking,
                message={
                    "message_type": "error",
                    "body": "Too much product in command",
                },
            )

        move_line.qty_done = quantity_to_set

        if move_line.qty_done == move_line.product_uom_qty:
            move_line.shopfloor_checkout_done = True
        else:
            move_line.shopfloor_checkout_done = False

        return self._response_for_scanned_product(picking, message)

    def list_stock_picking(self):
        """List stock.picking records available

        Returns a list of all the available records for the current picking
        type.

        Transitions:
        * manual_selection: to the selection screen
        """
        return self._response_for_manual_selection()

    def select(self, picking_id):
        """Select a stock picking for the scenario

        Used from the list of stock pickings (manual_selection), from there,
        the user can click on a stock.picking record which calls this method.

        The ``list_stock_picking`` returns only the valid records (same picking
        type, fully available, ...), but this method has to check again in case
        something changed since the list was sent to the client.

        Transitions:
        * manual_selection: stock.picking could finally not be selected (not
          available, ...)
        * summary: goes straight to this state used to set the moves as done when
          all the move lines with a reserved quantity have a 'quantity done'
        * select_line: the "normal" case, when the user has to put in pack/move
          lines
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_manual_selection(message=message)
        return self._select_picking(picking, "manual_selection")

    def scan_product(self, picking_id, barcode):
        """Adds 1 to a product quantity done

        Transitions:
        * scan_products: in all cases
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)

        # If there are more than one move_lines with the same product
        # just pick the first one that hasn't a quantity done equal to
        # it's target quantity
        move_lines = picking.move_line_ids.filtered(
            lambda l: l.product_id.barcode == barcode and not l.shopfloor_checkout_done
        )

        if len(move_lines) > 0:
            move_line = move_lines[0]
        else:
            return self._response_for_scanned_product(
                picking, message=self.msg_store.barcode_not_found()
            )

        quantity_to_set = move_line.qty_done + 1

        if quantity_to_set > move_line.product_uom_qty:
            return self._response_for_scanned_product(
                picking,
                message={
                    "message_type": "error",
                    "body": "Too much product in command",
                },
            )

        move_line.qty_done = quantity_to_set

        if move_line.qty_done == move_line.product_uom_qty:
            move_line.shopfloor_checkout_done = True
        else:
            move_line.shopfloor_checkout_done = False

        return self._response_for_scanned_product(picking, message)

    def _response_for_scanned_product(self, picking, message=None):
        return self._response(
            next_state="scan_products",
            data={"picking": self._data_for_stock_picking(picking)},
            message=message,
        )

    def done(self, picking_id, confirmation=False):
        """Set the moves as done

        If some lines have not the full ``qty_done`` or no destination package set,
        a confirmation is asked to the user.

        Transitions:
        * summary: in case of error
        * select_document: after done, goes back to start
        * confirm_done: confirm a partial
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)
        lines = picking.move_line_ids
        if not confirmation:
            if not all(line.qty_done == line.product_uom_qty for line in lines):
                return self._response_for_summary(
                    picking,
                    need_confirm=True,
                    message=self.msg_store.transfer_confirm_done(),
                )
            elif not all(line.shopfloor_checkout_done for line in lines):
                return self._response_for_summary(
                    picking,
                    need_confirm=True,
                    message={
                        "message_type": "warning",
                        "body": _("Remaining raw product not packed, proceed anyway?"),
                    },
                )
        picking.action_done()
        return self._response_for_select_document(
            message=self.msg_store.transfer_done_success(picking)
        )


class ShopfloorCheckoutScanAndPackValidator(Component):
    """Validators for the Checkout endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.checkout_scan_and_pack.validator"
    _usage = "checkout_scan_and_pack.validator"

    def scan_document(self):
        return {
            "barcode": {"required": True, "type": "string"},
            "skip": {"coerce": to_int, "required": False, "type": "integer"},
        }

    def list_stock_picking(self):
        return {}

    def select(self):
        return {"picking_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def scan_product(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def set_quantity(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "qty": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def list_packaging(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def done(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }


class ShopfloorCheckoutScanAndPackValidatorResponse(Component):
    """Validators for the Checkout endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.checkout_scan_and_pack.validator.response"
    _usage = "checkout_scan_and_pack.validator.response"

    _start_state = "select_document"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "select_document": {},
            "manual_selection": self._schema_selection_list,
            "select_line": self._schema_stock_picking_details,
            "scan_products": self._schema_stock_picking_details,
            "select_package": dict(
                self._schema_selected_lines,
                packing_info={"type": "string", "nullable": True},
                no_package_enabled={
                    "type": "boolean",
                    "nullable": True,
                    "required": False,
                },
            ),
            "change_quantity": self._schema_selected_lines,
            "select_dest_package": self._schema_select_package,
            "select_delivery_packaging": self._schema_select_delivery_packaging,
            "summary": self._schema_summary,
            "change_packaging": self._schema_select_packaging,
            "confirm_done": self._schema_confirm_done,
        }

    def _schema_stock_picking(self, lines_with_packaging=False):
        schema = self.schemas.picking()
        schema.update(
            {
                "move_lines": self.schemas._schema_list_of(
                    self.schemas.move_line(with_packaging=lines_with_packaging)
                )
            }
        )
        return {
            "picking": self.schemas._schema_dict_of(schema, required=True),
            "skip": {"type": "integer", "nullable": True},
        }

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
    def _schema_confirm_done(self):
        return self._schema_stock_picking(lines_with_packaging=True)

    @property
    def _schema_selection_list(self):
        return {
            "pickings": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.picking()},
            }
        }

    @property
    def _schema_select_package(self):
        return {
            "selected_move_lines": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
            "packages": {
                "type": "list",
                "schema": {
                    "type": "dict",
                    "schema": self.schemas.package(with_packaging=True),
                },
            },
            "picking": {"type": "dict", "schema": self.schemas.picking()},
        }

    @property
    def _schema_select_delivery_packaging(self):
        return {
            "packaging": self.schemas._schema_list_of(
                self.schemas.delivery_packaging()
            ),
        }

    @property
    def _schema_select_packaging(self):
        return {
            "picking": {"type": "dict", "schema": self.schemas.picking()},
            "package": {
                "type": "dict",
                "schema": self.schemas.package(with_packaging=True),
            },
            "packaging": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.packaging()},
            },
        }

    @property
    def _schema_selected_lines(self):
        return {
            "selected_move_lines": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
            "picking": {"type": "dict", "schema": self.schemas.picking()},
        }

    def scan_document(self):
        return self._response_schema(
            next_states={"select_document", "select_line", "summary", "scan_products"}
        )

    def list_stock_picking(self):
        return self._response_schema(next_states={"manual_selection"})

    def select(self):
        return self._response_schema(
            next_states={"scan_products", "manual_selection", "summary", "select_line"}
        )

    def scan_line(self):
        return self._response_schema(
            next_states={"select_line", "select_package", "summary"}
        )

    def scan_product(self):
        return self._response_schema(next_states={"scan_products"})

    def set_quantity(self):
        return self._response_schema(next_states={"scan_products"})

    def list_packaging(self):
        return self._response_schema(next_states={"change_packaging", "summary"})

    def done(self):
        return self._response_schema(next_states={"summary", "confirm_done"})
