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
                v-if="state_is('choosingContact')"
                @select-contact="state.onSelectContact"
                :stateData="state"
                />
            <choosing-reception-picking
                v-if="state_is('choosingPicking')"
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
    data: function() {
        return {
            usage: "reception",
            initial_state_key: "choosingContact",
            scan_destination_qty: 0,
            errorNotFound: undefined,
            states: {
                choosingContact: {
                    onSelectContact: () => {
                        this.wait_call(
                            this.odoo.call('list_stock_picking'),
                            (result) => {
                                result.data.choosingPicking = result.data[result.next_state];
                                delete result.data[result.next_state];
                                result.next_state = "choosingPicking"
                                this.on_call_success(result);
                            },
                        );
                    },
                    fields: [
                        {
                            label: "Total receipt",
                            path: "picking_count",
                        },
                    ],
                    contacts: [
                        {
                            name: "Vendeur 1",
                            picking_count: 2,
                            id: 0,
                        },
                        {
                            name: "Vendeur 2",
                            picking_count: 1,
                            id: 1,
                        },
                    ],
                },
                choosingPicking: {
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
                select_line: {
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
