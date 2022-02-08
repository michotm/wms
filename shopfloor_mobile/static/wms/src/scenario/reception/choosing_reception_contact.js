/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("choosing-reception-contact", {
    props: ["partners", "fields", "searchPartner"],
    template: `
        <div>
            <searchbar
                :input_placeholder="scan_placeholder"
                v-on:found="searchPartner"
            />
            <contact-list
                v-if="partners && partners.length > 0"
                v-on="$listeners"
                :searchPartnerString="searchPartnerString"
                :fields="fields"
                :contacts="partners"
                />
            <div
                v-if="!partners || partners.length === 0"
                >
                There is no reception to process
            </div>
        </div>
    `,
    methods: {
        searchPartner: function({text}) {
            this.searchPartnerString = text;
        },
    },
    data: () => ({
        searchPartnerString: "",
        scan_placeholder: "Search contact",
    }),
});
