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
                <detail-simple-location
                    v-if="state_is('start')"
                    v-for="location in state.data.input_locations"
                    :key="location.id"
                    :record="location"
                    />
                <stock-batch-scan-products
                    v-if="state_is('scan_products')"
                    data="state.data.scan_products"
                />
        </Screen>
        `,
    computed: {
    },
    methods: {
        screen_title: function() {
            return "Input Stock Transfer";
        },
    },
    data: function() {
        return {
            usage: "stock_batch_transfer",
            initial_state_key: "start",
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
                        this.wait_call(
                            this.odoo.call("scan_location", {barcode: text})
                        );
                    },
                },
            },
        };
    },
};

process_registry.add("stock_batch_transfer", StockBatchTransfer);

export default StockBatchTransfer;
