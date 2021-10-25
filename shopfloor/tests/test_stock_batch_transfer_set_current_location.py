# Copyright 2020 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_stock_batch_transfer_base import StockBatchTransferCommonCase


class StockBatchTransferSetCurrentLocation(StockBatchTransferCommonCase):
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

    def _test_set_current_location(self, barcode, current_source_location_id, response_expected):
        response = self.service.dispatch(
            "set_current_location",
            params={
                "barcode": barcode,
                "current_source_location_id": current_source_location_id,
            },
        )
        self.assert_response(
            response,
            message=response_expected["message"],
            next_state=response_expected["next_state"],
            data=response_expected["data"],
        )
        return response

    def test_set_current_location_wrong_location(self):
        self._test_set_current_location(
            "NOT_A_BARCODE",
            self.picking.location_id.id,
            response_expected={
                "message": {
                    "message_type": "error",
                    "body": "You cannot place it here",
                },
                "next_state": "scan_products",
                "data": self.ANY,
            }
        )

    def test_set_current_location_ok(self):
        self._test_set_current_location(
            self.stock_location.barcode,
            self.picking.location_id.id,
            response_expected={
                "message": None,
                "next_state": "scan_products",
                "data": {'id': self.stock_location.id,
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
                                               'qty_done': 0.0,
                                               'quantity': 10.0}],
                               'move_lines_done': None,
                               'selected_location': self.stock_location.id},
            }
        )
