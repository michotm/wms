/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const StockBatchTransfer = {
    mixins: [ScenarioBaseMixin],
    template: `
        <Screen :screen_info="screen_info">
            <template v-slot:header>
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
            <searchbar
                v-if="state.on_scan"
                v-on:found="on_scan"
                :input_placeholder="search_input_placeholder"
                />
                <div
                v-if="state_is('start') && (state.data.input_locations.length === 0)"
                >
                    There is no transfer to process
                </div>
                <detail-simple-location
                    @click="state.on_scan({text: location.barcode})"
                    v-if="state_is('start')"
                    v-for="location in state.data.input_locations"
                    :key="location.id"
                    :record="location"
                    />
                <batch-product-by-dest
                    v-if="state_is('scan_products')"
                    :moveLines="state.data.move_lines"
                    :fields="state.fields"
                    :lastScanned="lastScanned"
                    :selectedLocation="state.data.selected_location"
                    :currentLocation="state.data.selected_location"
                    :lastPickedLines="lastPickedLines || []"
                    />
        </Screen>
        `,
    computed: {
        currentDestLocation: function() {
            return this.state.data.selected_location;
        },
        currentSourceLocation: function() {
            return this.state.data.id;
        },
    },
    methods: {
        screen_title: function() {
            return "Input Stock Transfer";
        },
    },
    beforeUnmount() {
        this.lastScanned = null;
        this.lastPickedLines = null;
    },
    data: function() {
        return {
            usage: "stock_batch_transfer",
            initial_state_key: "start",
            lastScanned: null,
            lastPickedLines: null,
            states: {
                start: {
                    display_info: {
                        title: "Choose an input sublocation to stock",
                        scan_placeholder: "Scan input location or sublocation",
                    },
                    on_scan: ({text}) => {
                        this.wait_call(
                            this.odoo.call("scan_location", {barcode: text})
                        );
                    },
                    enter: () => {
                        this.wait_call(this.odoo.call("list_input_location"));
                    },
                },
                scan_products: {
                    display_info: {
                        title: "Go to the first location",
                        scan_placeholder: "Scan a destination location",
                    },
                    on_scan: ({text}) => {
                        const intInText =
                            "" + text == parseInt(text, 10) && parseInt(text, 10);

                        if (this.currentDestLocation) {
                            if (this.lastScanned) {
                                if (intInText && intInText !== 0) {
                                    this.wait_call(
                                        this.odoo.call("set_product_qty", {
                                            barcode: this.lastScanned,
                                            current_source_location_id: this
                                                .currentSourceLocation,
                                            dest_location_id: this.currentDestLocation,
                                            qty: intInText,
                                        })
                                    );
                                } else if (text === this.lastScanned) {
                                    this.wait_call(
                                        this.odoo.call("drop_product_to_location", {
                                            barcode: text,
                                            current_source_location_id: this
                                                .currentSourceLocation,
                                            dest_location_id: this.currentDestLocation,
                                        }),
                                        ({message}) => {
                                            if (
                                                !message ||
                                                message.message_type !== "error"
                                            ) {
                                                this.lastScanned = text;
                                            }
                                        }
                                    );
                                } else {
                                    this.wait_call(
                                        this.odoo.call("set_product_destination", {
                                            barcode: text,
                                            product_barcode: this.lastScanned,
                                            current_source_location_id: this
                                                .currentSourceLocation,
                                            dest_location_id: this.currentDestLocation,
                                        }),
                                        ({message, data}) => {
                                            if (
                                                message &&
                                                message.message_type === "success"
                                            ) {
                                                this.lastScanned = null;
                                                this.lastPickedLines = data.scan_products.move_lines_done;
                                            }
                                        }
                                    );
                                }
                            } else {
                                this.wait_call(
                                    this.odoo.call("drop_product_to_location", {
                                        barcode: text,
                                        current_source_location_id: this
                                            .currentSourceLocation,
                                        dest_location_id: this.currentDestLocation,
                                    }),
                                    ({message}) => {
                                        if (
                                            !message ||
                                            message.message_type !== "error"
                                        ) {
                                            this.lastScanned = text;
                                        }
                                    }
                                );
                            }
                        } else {
                            this.wait_call(
                                this.odoo.call("set_current_location", {
                                    barcode: text,
                                    current_source_location_id: this
                                        .currentSourceLocation,
                                })
                            );
                        }
                    },
                    fields: [
                        {path: "supplierCode", label: "Vendor code", klass: "loud"},
                        {path: "qty", label: "Quantity"},
                        {path: "qtyDone", label: "Done"},
                        {path: "picking_dest.name", label: "Picking destination"},
                        {path: "dest.name", label: "Should be put in"},
                    ],
                },
            },
        };
    },
};

process_registry.add("stock_batch_transfer", StockBatchTransfer);

export default StockBatchTransfer;
