/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const InputStockTransfer = {
    mixins: [ScenarioBaseMixin],
    /*
        /!\ IMPORTANT: we use many times the same component
        (eg: manual-select or detail-picking-select)
        and to make sure they don't get cached together
        we MUST call them using `:key` to make them unique!
        If you don't, you'll have severe problems of data being shared
        between each instances. This is the real problem:
        you assume to have different instance but indeed you get only 1
        which is reused every time!
    */
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
            usage: "input_stock_transfer",
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
            },
        };
    },
};

process_registry.add("input_stock_transfer", InputStockTransfer);

export default InputStockTransfer;
