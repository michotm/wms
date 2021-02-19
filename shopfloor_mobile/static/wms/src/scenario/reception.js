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
                :partners="state.data.partners"
                :fields="state.fields"
                />
            <choosing-reception-picking
                v-if="state_is('manual_selection')"
                @select-picking="state.onSelectPicking"
                :stateData="state"
                />
            <reception-scanning-product
                v-if="state_is('scan_products')"
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
        if (!this.state_get_data('start').partners) {
            this.wait_call(
                this.odoo.call('list_vendor_with_pickings'),
            );
        }
    },
    computed() {
        partnerId: function() {
            return this.state.data.id;
        },
    },
    data: function() {
        return {
            partnerId: null,
            usage: "reception",
            initial_state_key: "start",
            scan_destination_qty: 0,
            errorNotFound: undefined,
            states: {
                start: {
                    onSelectContact: (partner_id) => {
                        this.wait_call(
                            this.odoo.call('list_move_lines', {partner_id}),
                        );
                    },
                    fields: [
                        {
                            label: "Total receipt",
                            path: "picking_count",
                        },
                    ],
                },
                scan_products: {
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
                    onScanProduct: ({text: barcode}) => {
                        if (this.state.data.move_lines_picking.length <= 0) {
                            this.wait_call(
                                this.odoo.call('scan_product', {partner_id: this.partnerId, barcode})
                            );
                        }
                        else {
                            this.wait_call(
                                this.odoo.call('increase_quantity', {
                                    partner_id: this.partnerId,
                                    barcode,
                                    move_lines_picking: this.state.data.move_lines_picking.map(
                                        line => line.id,
                                    ),
                                })
                            );
                        }
                    },
                }
            },
        };
    },
};

process_registry.add("reception", Reception);

export default Reception;
