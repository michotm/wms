# Copyright 2020 Akretion (https://akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .common import CommonCase


class ReceptionCommonCase(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_reception")
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        cls.wh = cls.profile.warehouse_id
        cls.picking_type = cls.menu.picking_type_ids

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            self.service = work.component(usage="reception")

    def _stock_picking_data(self, picking, **kw):
        return self.service._data_for_stock_picking(picking, **kw)


class ReceptionCase(ReceptionCommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking1 = picking = cls._create_picking(
            lines=[
                (cls.product_a, 10),
                (cls.product_b, 10),
                (cls.product_c, 10),
                (cls.product_d, 10),
            ]
        )
        cls.pack1_moves = picking.move_lines[:2]
        cls.pack2_moves = picking.move_lines[2]
        cls.raw_move = picking.move_lines[3]
        cls._fill_stock_for_moves(cls.pack1_moves, in_package=True)
        cls._fill_stock_for_moves(cls.pack2_moves, in_package=True)
        cls._fill_stock_for_moves(cls.raw_move)
        picking.action_assign()

        cls.picking2 = picking = cls._create_picking(
            lines=[
                (cls.product_a, 10),
                (cls.product_d, 10),
            ]
        )
        for move in picking.move_lines:
            cls._fill_stock_for_moves(move)
        picking.action_assign()

        cls.picking3 = picking = cls._create_picking(
            lines=[
                (cls.product_a, 10),
                (cls.product_b, 10),
            ]
        )
        for move in picking.move_lines:
            cls._fill_stock_for_moves(move)
        picking.action_assign()

    def test_scan_document_by_picking(self):
        picking = self.picking1
        response = self.service.dispatch(
            "scan_document",
            params={"barcode": picking.name},
        )
        self.assert_response(
            response,
            next_state="select_line",
            data={"picking": self._stock_picking_data(picking)},
        )

    def test_scan_document_by_product(self):
        expected = self.picking1 | self.picking3
        response = self.service.dispatch(
            "scan_document",
            params={"barcode": self.product_b.barcode},
        )
        self.assert_response(
            response,
            next_state="manual_selection",
            data={"pickings": self.data.pickings(expected)},
        )
