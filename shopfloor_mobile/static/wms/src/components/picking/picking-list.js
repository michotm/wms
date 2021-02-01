/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("picking-list", {
    props: ["pickings", "fields"],
    template: `
        <div>
            <detail-picking
                v-on="$listeners"
                :fields="fields"
                :record="picking"
                v-for="picking in pickings"
                :options="{fields: fields, full_detail: true, on_title_action: () => $emit('select-picking', picking.id)}"
                :key="picking.id"
                />
        </div>
    `,
});
