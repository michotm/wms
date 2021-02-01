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
                v-on:select-contact="state.onSelect"
                :stateData="state"
                />
            <choosing-reception-picking
                v-if="state_is('choosingPicking')"
                :stateData="state"
                />
        </Screen>
    `,
    data: function() {
        return {
            usage: "reception",
            initial_state_key: "choosingContact",
            scan_destination_qty: 0,
            states: {
                choosingContact: {
                    onSelect: () => {
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
                    fields: [
                        {
                            label: "Partner",
                            path: "partner.name",
                        },
                    ],
                },
            },
        };
    },
};

process_registry.add("reception", Reception);

export default Reception;
