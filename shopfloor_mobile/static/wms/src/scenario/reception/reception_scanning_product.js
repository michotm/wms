/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("reception-scanning-product", {
    props: ["stateData"],
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
                :products="stateData.scanned"
                />
            <div
                v-if="stateData.scanned.length == 0 && !stateData.data.productChooseQuantity"
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
