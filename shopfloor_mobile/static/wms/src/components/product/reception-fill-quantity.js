/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("reception-fill-quantity", {
    props: {product: Object, fields: Array},
    template: `
    <div>
      <item-detail-card :record="product" :options="{fields: fields}" v-bind="$attrs">
        <template v-slot:subtitle>
            <v-form>
                <v-text-field
                    label="Quantity"
                    v-model="quantity"
                    :rules=[rules.required]
                    >
                </v-text-field>
            </v-form>
        </template>
      </item-detail-card>
      </div>
    `,
    mounted() {
        this.quantity = this.product.qty;
    },
    data() {
        return {
            quantity: 0,
            rules: {
                required: value => !!value || "Required",
            },
        };
    },
});
