/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("choosing-reception-picking", {
    props: ["stateData"],
    template: `
        <div>
            <searchbar
                :input_placeholder="scan_placeholder"
                />
            <picking-list
                :pickings="stateData.data.pickings"
                />
        </div>
    `,
    mounted: function() {
        console.log(this.$props.stateData);
    },
    data: () => ({
        scan_placeholder: "Scan product",
    })
});
