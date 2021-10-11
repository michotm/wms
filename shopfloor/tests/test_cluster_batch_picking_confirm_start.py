# Copyright 2020 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_cluster_batch_picking_base import ClusterBatchPickingCommonCase
from copy import deepcopy

class ClusterBatchPickingConfirmStartCase(ClusterBatchPickingCommonCase):
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

    def _test_confirm_start(self, picking_batch_id, response_expected):
        response = self.service.dispatch(
            "confirm_start",
            params={
                "picking_batch_id": picking_batch_id,
            },
        )
        self.assert_response(
            response,
            message=response_expected.get("message"),
            next_state=response_expected.get("next_state"),
            data=response_expected.get("data"),
        )
        return response

    def test_confirm_start_BatchDoesNotExist(self):
        self._test_confirm_start(
            -1,
            response_expected={
                "message": {
                    "message_type": "error",
                    "body": "The record you were working on does not exist anymore.",
                },
                "next_state": "start",
                "data": {},
            }
        )

    def test_confirm_start_with_next_line(self):

        self._simulate_batch_selected(self.batch, fill_stock=True)

        expected_data = {
                    "id": self.ANY,
                    "move_lines": [
                        {
                            "done": False,
                            "id": self.ANY,
                            "location_dest": {"barcode": "PACKING",
                                              "id": self.ANY,
                                              "name": "Packing "
                                                      "Zone"},
                            "location_src": {"barcode": "WH-STOCK",
                                             "id": self.ANY,
                                             "name": "Stock"},
                            "lot": None,
                            "package_dest": None,
                            "package_src": None,
                            "picking": {"carrier": None,
                                        "id": self.ANY,
                                        "move_line_count": 1,
                                        "name": self.ANY,
                                        "note": None,
                                        "origin": "test",
                                        "partner": {"id": self.ANY,
                                                    "name": "Customer"},
                                        "scheduled_date": self.ANY,
                                        "weight": 20.0},
                            "priority": "0",
                            "product": {"barcode": "A",
                                        "barcodes": [{"id": self.ANY,
                                                      "name": "A"}],
                                        "default_code": "A",
                                        "display_name": "[A] "
                                                        "Product "
                                                        "A",
                                        "id": self.ANY,
                                        "name": "Product A",
                                        "packaging": [],
                                        "supplier_code": "",
                                        "uom": {"factor": 1.0,
                                                "id": self.ANY,
                                                "name": "Units",
                                                "rounding": 0.01}},
                            "qty_done": 0.0,
                            "quantity": 10.0,
                            "suggested_location_dest": [],
                            "suggested_package_dest": []
                        }
                    ]
                }

        self._test_confirm_start(
            self.batch.id,
            response_expected={
                "message":None,
                "next_state": "scan_products",
                "data": expected_data,
            }
        )

    def test_confirm_start_without_next_line(self):
        self._simulate_batch_selected(self.batch, fill_stock=True)
        move_line = self.batch.mapped("move_line_ids")
        move_line.qty_done = 10.0
        move_line.location_dest_id = self.packing_sublocation.id

        self._test_confirm_start(
            self.batch.id,
            response_expected={
                "message": self.msg_store.batch_transfer_complete(),
                "next_state": "start",
                "data": {},
            }
        )
