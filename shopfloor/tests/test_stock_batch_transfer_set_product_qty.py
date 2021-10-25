# Copyright 2020 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_stock_batch_transfer_base import StockBatchTransferCommonCase


class StockBatchTransferSetProductQty(StockBatchTransferCommonCase):
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

    def _test_set_product_qty(self, barcode, current_source_location_id, dest_location_id, qty, response_expected):
        response = self.service.dispatch(
            "set_product_qty",
            params={
                "barcode": barcode,
                "current_source_location_id": current_source_location_id,
                "dest_location_id": dest_location_id,
                "qty": qty,
            },
        )
        self.assert_response(
            response,
            message=response_expected["message"],
            next_state=response_expected["next_state"],
            data=response_expected["data"],
        )
        return response

    def test_set_product_qty_wrong_barcode(self):
        self._test_set_product_qty(
            "NOT_A_BARCODE",
            self.stock_location.id,
            self.stock_location.id,
            1,
            response_expected={
                "message": {
                    "message_type": "error",
                    "body": "Barcode not found",
                },
                "next_state": "scan_products",
                "data": self.ANY,
            }
        )

    def test_set_product_qty_wrong_current_location(self):
        self._test_set_product_qty(
            self.picking.move_line_ids[0].product_id.barcode,
            -1,
            self.stock_location.id,
            1,
            response_expected={
                "message": {
                    "message_type": "error",
                    "body": "Barcode not found",
                },
                "next_state": "scan_products",
                "data": self.ANY,
            }
        )

    def test_set_product_qty_wrong_dest_location(self):
        self._test_set_product_qty(
            self.picking.move_line_ids[0].product_id.barcode,
            self.stock_location.id,
            -1,
            1,
            response_expected={
                "message": {
                    "message_type": "error",
                    "body": "Barcode not found",
                },
                "next_state": "scan_products",
                "data": self.ANY,
            }
        )

    def test_set_product_qty_wrong_dest_location(self):
        self._test_set_product_qty(
            self.picking.move_line_ids[0].product_id.barcode,
            self.stock_location.id,
            -1,
            1,
            response_expected={
                "message": {
                    "message_type": "error",
                    "body": "Barcode not found",
                },
                "next_state": "scan_products",
                "data": self.ANY,
            }
        )

