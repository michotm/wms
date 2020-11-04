/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("reception-scanning-product", {
    props: ["stateData"],
    template: `
        <div>
            <reception-info-bar :reception="stateData"/>
            <searchbar
                :input_placeholder="scan_placeholder"
                />
            <reception-product-list
                v-on="$listeners"
                :products="stateData.data.pickings"
                >
        </div>
    `,
    data: () => ({
        scan_placeholder: "Scan product",
    })
});
