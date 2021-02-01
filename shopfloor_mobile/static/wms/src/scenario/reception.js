/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "./mixins.js";
import {process_registry} from "../services/process_registry.js";

const Reception = {
    mixins: [ScenarioBaseMixin],
    template: `
        <Screen :screen_info="screen_info">
            <choosing-reception-contact
                v-if="state_is('start')"
                @select-contact="state.onSelectContact"
                :stateData="state"
                />
            <choosing-reception-picking
                v-if="state_is('manual_selection')"
                @select-picking="state.onSelectPicking"
                :stateData="state"
                />
            <reception-scanning-product
                v-if="state_is('select_line')"
                :stateData="state"
                @found="state.onScanProduct"
                />
            <v-dialog
                v-model="errorNotFound"
                >
                <v-card>
                    <v-card-title class="headline">Product not found</v-card-title>
                    <v-card-text>This product is not in the receipt</v-card-text>
                    <v-card-actions>
                        <v-btn depressed @click="errorNotFound = undefined">Ok</v-btn>
                    </v-card-actions>
                </v-card>
            </v-dialog>
        </Screen>
    `,
    mounted() {
        this.wait_call(
            this.odoo.call('list_vendor_with_pickings'),
        );
    },
    data: function() {
        return {
            usage: "reception",
            initial_state_key: "start",
            scan_destination_qty: 0,
            errorNotFound: undefined,
            states: {
                start: {
                    onSelectContact: () => {
                        this.wait_call(
                            this.odoo.call('list_stock_picking'),
                        );
                    },
                    fields: [
                        {
                            label: "Total receipt",
                            path: "picking_count",
                        },
                    ],
                },
                manual_selection: {
                    onSelectPicking: (picking_id) => {
                        this.wait_call(
                            this.odoo.call('select', {picking_id})
                        );
                    },
                    fields: [
                        {
                            label: "Partner",
                            path: "partner.name",
                        },
                    ],
                },
                list_products_scanned: {
                    scanned: [],
                    productQtyFields: [
                        {
                            label: "Qty",
                            path: "qty",
                        },
                    ],
                    productFields: [
                        {
                            label: "Qty",
                            path: "qtyDone",
                        },
                    ],
                    receptionFields: [
                        {
                            label: "Partner",
                            path: "partner.name",
                        },
                    ],
                    onScanProduct: ({text: scanData}) => {
                        // We check if the product is in the receipt
                        let product = this.state.data.picking.move_lines.find(line => {
                            return line.product.barcode === scanData;
                        });

                        if (!product) {
                            this.errorNotFound = scanData;
                            return;
                        }

                        let productModel = {
                            name: product.product.name,
                            qty: 1,
                        };

                        this.state_set_data({...this.state.data, productChooseQuantity: productModel});
                    },
                }
            },
        };
    },
};

process_registry.add("reception", Reception);

export default Reception;
