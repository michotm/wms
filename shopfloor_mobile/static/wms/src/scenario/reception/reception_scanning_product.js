/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("reception-scanning-product", {
    props: ["stateData"],
    computed: {
        moveLines: function() {
            const moveLines = this.stateData.data.move_lines_picked
            moveLines.unshift(...this.stateData.data.move_lines_picking);

            return moveLines
                .map(move_line => ({
                    qtyDone: move_line.qty_done,
                    name: move_line.product.display_name,
                }));
        },
    },
    template: `
        <div>
            <reception-info-bar
                :reception="stateData.data.picking"
                :fields="stateData.receptionFields"
                />
            <searchbar
                :input_placeholder="scan_placeholder"
                v-on="$listeners"
                />
            <reception-fill-quantity
                :fields="stateData.productFields"
                :product="stateData.data.productChooseQuantity"
                v-if="stateData.data.productChooseQuantity"
                >
            </reception-fill-quantity>
            <reception-product-list
                v-on="$listeners"
                :fields="stateData.productFields"
                :products="moveLines"
                />
            <div
                v-if="moveLines.length == 0"
                >
                Start scanning product to start receiving
            </div>
        </div>
    `,
    data: () => ({
        scan_placeholder: "Scan product",
    }),
    updated: () => {
        console.log("updated");
    }
});
