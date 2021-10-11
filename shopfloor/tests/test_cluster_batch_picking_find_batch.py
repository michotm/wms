# Copyright 2020 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_cluster_batch_picking_base import ClusterBatchPickingCommonCase


class ClusterBatchPickingFindBatchCase(ClusterBatchPickingCommonCase):
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

    def _test_find_batch(self, response_expected):
        response = self.service.dispatch(
            "find_batch",
            params={},
        )
        self.assert_response(
            response,
            message=response_expected["message"],
            next_state=response_expected["next_state"],
            data=response_expected["data"],
        )
        return response

    def test_find_batch_no_selected(self):
        self._test_find_batch(
            response_expected={
                "message": {
                    "message_type": "info",
                    "body": "No more work to do, please create a new batch transfer",
                },
                "next_state": "start",
                "data": {},
            }
        )

    def test_find_batch_unselected(self):
        self._simulate_batch_selected(self.batch, in_package=False, in_lot=False, fill_stock=True)

        self._test_find_batch(
            response_expected={
                "message": None,
                "next_state": "confirm_start",
                "data": self._data_for_batch(self.batch)
            }
        )

