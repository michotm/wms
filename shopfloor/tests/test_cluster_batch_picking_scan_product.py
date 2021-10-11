# Copyright 2020 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_cluster_batch_picking_base import ClusterBatchPickingCommonCase


class ClusterBatchPickingScanProductCase(ClusterBatchPickingCommonCase):
    """Tests covering the /change_pack_lot endpoint

    Only simple cases are tested to check the flow of responses on success and
    error, the "change.package.lot" component is tested in its own tests.
    """

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.batch = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=10)]]
        )

    def _test_scan_product(self, response_expected, picking_batch_id, move_line_id, location_id, barcode):
        response = self.service.dispatch(
            "scan_product",
            params={
                "picking_batch_id": picking_batch_id,
                "move_line_id": move_line_id,
                "location_id": location_id,
                "barcode": barcode
            },
        )
        self.assert_response(
            response,
            message=response_expected["message"],
            next_state=response_expected["next_state"],
            data=response_expected["data"],
        )
        return response

    def test_scan_product_wrong_location(self):
        self._simulate_batch_selected(self.batch, fill_stock=True)
        self._test_scan_product(
            {
                "message": {
                    "message_type": "error",
                    "body": "Product is not in source location",
                },
                "next_state": "scan_products",
                "data": self.ANY,
            },
            self.batch.id,
            self.batch.move_line_ids.id,
            -1,
            self.batch.move_line_ids.product_id.barcode
        )

    def test_scan_product_too_much_product(self):
        self._simulate_batch_selected(self.batch, fill_stock=True)
        self.batch.move_line_ids.qty_done = self.batch.move_line_ids.product_uom_qty

        self._test_scan_product(
            {
                "message": {
                    "message_type": "error",
                    "body": "Too much product in command",
                },
                "next_state": "scan_products",
                "data": self.ANY,
            },
            self.batch.id,
            self.batch.move_line_ids.id,
            self.batch.move_line_ids.location_id.id,
            self.batch.move_line_ids.product_id.barcode
        )

    def test_scan_product_success(self):
        self._simulate_batch_selected(self.batch, fill_stock=True)

        expected_data = {
            'id': self.ANY,
            'move_lines': [
                {
                    'done': False,
                    'id': self.ANY,
                    'location_dest': {'barcode': 'PACKING',
                                      'id': self.ANY,
                                      'name': 'Packing '
                                              'Zone'},
                    'location_src': {'barcode': 'WH-STOCK',
                                     'id': self.ANY,
                                     'name': 'Stock'},
                    'lot': None,
                    'package_dest': None,
                    'package_src': None,
                    'picking': {'carrier': None,
                                'id': self.ANY,
                                'move_line_count': 1,
                                'name': self.ANY,
                                'note': None,
                                'origin': 'test',
                                'partner': {'id': self.ANY,
                                            'name': 'Customer'},
                                'scheduled_date': self.ANY,
                                'weight': 20.0},
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
                    'quantity': 10.0,
                    'suggested_location_dest': [],
                    'suggested_package_dest': []
                }
            ]
        }

        self._test_scan_product(
            {
                "message": None,
                "next_state": "scan_products",
                "data": expected_data,
            },
            self.batch.id,
            self.batch.move_line_ids.id,
            self.batch.move_line_ids.location_id.id,
            self.batch.move_line_ids.product_id.barcode
        )

