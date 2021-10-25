# Copyright 2020 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_stock_batch_transfer_base import StockBatchTransferCommonCase


class StockBatchTransferDropProductToLocation(StockBatchTransferCommonCase):
    """Tests covering the /change_pack_lot endpoint

    Only simple cases are tested to check the flow of responses on success and
    error, the "change.package.lot" component is tested in its own tests.
    """

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.picking = cls._create_picking()
        cls._fill_stock_for_moves(cls.picking.move_lines, in_package=False)
        cls.picking.action_assign()
        cls.picking.move_line_ids[1].write({"qty_done": 10.0})

    def _test_drop_product_to_location(self, barcode, current_source_location_id, dest_location_id, response_expected):
        response = self.service.dispatch(
            "drop_product_to_location",
            params={
                "barcode": barcode,
                "current_source_location_id": current_source_location_id,
                "dest_location_id": dest_location_id,
            },
        )
        self.assert_response(
            response,
            message=response_expected["message"],
            next_state=response_expected["next_state"],
            data=response_expected["data"],
        )
        return response

    def test_drop_product_to_location_barcode_not_found(self):
        self._test_drop_product_to_location(
            "NOT_A_BARCODE",
            self.stock_location.id,
            -1,
            response_expected={
                "message": {
                    "message_type": "error",
                    "body": "Barcode not found",
                },
                "next_state": "scan_products",
                "data": self.ANY,
            }
        )

    def test_drop_product_to_location_ok(self):
        self._test_drop_product_to_location(
            self.picking.move_line_ids[0].product_id.barcode,
            self.stock_location.id,
            self.stock_location.id,
            response_expected={
                "message": None,
                "next_state": "scan_products",
                "data": {
                    "id": self.stock_location.id,
                   'move_lines': [{'done': False,
                                   'id': self.ANY,
                                   'location_dest': {'barcode': 'WH-STOCK',
                                                     'id': self.ANY,
                                                     'name': 'Stock'},
                                   'location_src': {'barcode': 'WH-STOCK',
                                                    'id': self.ANY,
                                                    'name': 'Stock'},
                                   'lot': None,
                                   'package_dest': None,
                                   'package_src': None,
                                   'picking': {'carrier': None,
                                               'id': self.ANY,
                                               'move_line_count': 2,
                                               'name': self.ANY,
                                               'note': None,
                                               'origin': None,
                                               'partner': {'id': self.ANY,
                                                           'name': 'Customer'},
                                               'scheduled_date': self.ANY,
                                               'weight': 50.0},
                                   'priority': '0',
                                   'product': {'barcode': 'A',
                                               'barcodes': [{'id': self.ANY,
                                                             'name': 'A'}],
                                               'default_code': 'A',
                                               'display_name': '[A] '
                                                               'Product '
                                                               'A',
                                               'id': self.ANY,
                                               'name': 'Product A',
                                               'packaging': [],
                                               'supplier_code': '',
                                               'uom': {'factor': 1.0,
                                                       'id': self.ANY,
                                                       'name': 'Units',
                                                       'rounding': 0.01}},
                                   'qty_done': 1.0,
                                   'quantity': 10.0},
                                  {'done': False,
                                   'id': self.ANY,
                                   'location_dest': {'barcode': 'WH-STOCK',
                                                     'id': self.ANY,
                                                     'name': 'Stock'},
                                   'location_src': {'barcode': 'WH-STOCK',
                                                    'id': self.ANY,
                                                    'name': 'Stock'},
                                   'lot': None,
                                   'package_dest': None,
                                   'package_src': None,
                                   'picking': {'carrier': None,
                                               'id': self.ANY,
                                               'move_line_count': 2,
                                               'name': self.ANY,
                                               'note': None,
                                               'origin': None,
                                               'partner': {'id': self.ANY,
                                                           'name': 'Customer'},
                                               'scheduled_date': self.ANY,
                                               'weight': 50.0},
                                   'priority': '0',
                                   'product': {'barcode': 'B',
                                               'barcodes': [{'id': self.ANY,
                                                             'name': 'B'}],
                                               'default_code': 'B',
                                               'display_name': '[B] '
                                                               'Product '
                                                               'B',
                                               'id': self.ANY,
                                               'name': 'Product B',
                                               'packaging': [],
                                               'supplier_code': '',
                                               'uom': {'factor': 1.0,
                                                       'id': self.ANY,
                                                       'name': 'Units',
                                                       'rounding': 0.01}},
                                   'qty_done': 10.0,
                                   'quantity': 10.0}],
                    "move_lines_done": None,
                    "selected_location": self.stock_location.id,
                    "selected_product": [self.picking.move_line_ids[0].product_id.barcode]
                },
            }
        )

    def test_drop_product_to_location_too_much_product(self):

        self._test_drop_product_to_location(
            self.picking.move_line_ids[1].product_id.barcode,
            self.stock_location.id,
            self.stock_location.id,
            response_expected={
                "message": {
                    'message_type': 'error',
                    'body': 'This operation does not exist anymore.',
                },
                "next_state": "scan_products",
                "data": {
                    "id": self.stock_location.id,
                   'move_lines': [{'done': False,
                                   'id': self.ANY,
                                   'location_dest': {'barcode': 'WH-STOCK',
                                                     'id': self.ANY,
                                                     'name': 'Stock'},
                                   'location_src': {'barcode': 'WH-STOCK',
                                                    'id': self.ANY,
                                                    'name': 'Stock'},
                                   'lot': None,
                                   'package_dest': None,
                                   'package_src': None,
                                   'picking': {'carrier': None,
                                               'id': self.ANY,
                                               'move_line_count': 2,
                                               'name': self.ANY,
                                               'note': None,
                                               'origin': None,
                                               'partner': {'id': self.ANY,
                                                           'name': 'Customer'},
                                               'scheduled_date': self.ANY,
                                               'weight': 50.0},
                                   'priority': '0',
                                   'product': {'barcode': 'A',
                                               'barcodes': [{'id': self.ANY,
                                                             'name': 'A'}],
                                               'default_code': 'A',
                                               'display_name': '[A] '
                                                               'Product '
                                                               'A',
                                               'id': self.ANY,
                                               'name': 'Product A',
                                               'packaging': [],
                                               'supplier_code': '',
                                               'uom': {'factor': 1.0,
                                                       'id': self.ANY,
                                                       'name': 'Units',
                                                       'rounding': 0.01}},
                                   'qty_done': 0.0,
                                   'quantity': 10.0},
                                  {'done': False,
                                   'id': self.ANY,
                                   'location_dest': {'barcode': 'WH-STOCK',
                                                     'id': self.ANY,
                                                     'name': 'Stock'},
                                   'location_src': {'barcode': 'WH-STOCK',
                                                    'id': self.ANY,
                                                    'name': 'Stock'},
                                   'lot': None,
                                   'package_dest': None,
                                   'package_src': None,
                                   'picking': {'carrier': None,
                                               'id': self.ANY,
                                               'move_line_count': 2,
                                               'name': self.ANY,
                                               'note': None,
                                               'origin': None,
                                               'partner': {'id': self.ANY,
                                                           'name': 'Customer'},
                                               'scheduled_date': self.ANY,
                                               'weight': 50.0},
                                   'priority': '0',
                                   'product': {'barcode': 'B',
                                               'barcodes': [{'id': self.ANY,
                                                             'name': 'B'}],
                                               'default_code': 'B',
                                               'display_name': '[B] '
                                                               'Product '
                                                               'B',
                                               'id': self.ANY,
                                               'name': 'Product B',
                                               'packaging': [],
                                               'supplier_code': '',
                                               'uom': {'factor': 1.0,
                                                       'id': self.ANY,
                                                       'name': 'Units',
                                                       'rounding': 0.01}},
                                   'qty_done': 10.0,
                                   'quantity': 10.0}],
                    "move_lines_done": None,
                    "selected_location": self.stock_location.id,
                    "selected_product": [self.picking.move_line_ids[1].product_id.barcode]
                },
            }
        )
