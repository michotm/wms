# Copyright 2020 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_stock_batch_transfer_base import StockBatchTransferCommonCase


class StockBatchTransferScanLocation(StockBatchTransferCommonCase):
    """Tests covering the /change_pack_lot endpoint

    Only simple cases are tested to check the flow of responses on success and
    error, the "change.package.lot" component is tested in its own tests.
    """

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)

    def _test_scan_location(self, barcode, response_expected):
        picking = self._create_picking()
        self._fill_stock_for_moves(picking.move_lines, in_package=False)
        picking.action_assign()
        response = self.service.dispatch(
            "scan_location",
            params={"barcode": barcode},
        )
        self.assert_response(
            response,
            message=response_expected["message"],
            next_state=response_expected["next_state"],
            data=response_expected["data"],
        )
        return response

    def test_scan_location_no_location(self):
        self._test_scan_location(
            "NOT_A_BARCODE",
            response_expected={
                "message": {
                    "message_type": "error",
                    "body": "No location found for this barcode.",
                },
                "next_state": "start",
                "data": self.ANY,
            }
        )

    def test_scan_location_location_found(self):
        self._test_scan_location(
            self.stock_location.barcode,
            response_expected={
                "message": {
                    "message_type": "success",
                    "body": "WH/Stock location selected".format(),
                },
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
                               'selected_location': None},
            }
        )
