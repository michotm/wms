/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("reception-info-bar", {
    props: ["reception", "fields"],
    template: `
        <div>
            <item-detail-card
                :record="reception"
                :options="{fields: fields}"
            />
        </div>
    `,
});
