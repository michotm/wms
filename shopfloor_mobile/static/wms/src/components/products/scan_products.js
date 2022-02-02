/**
 * Copyright 2020 Akretion SA (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

/* eslint-disable strict */
Vue.component("scan-products", {
    props: ["packing", "products", "fields", "lastScanned"],
    methods: {
        isLastScanned(product) {
            return product && product.id === this.lastScanned;
        },
        formatProduct(products) {
            return products
                .map(prod => ({
                    id: prod.id,
                    name: prod.product.display_name,
                    qty: prod.quantity,
                    qtyDone: prod.qty_done,
                    done: prod.done,
                    barcodes: prod.product.barcodes.map(b => b.name),
                    supplierCode: prod.product.supplier_code,
                }))
                .sort((a, b) => (a.done && !this.isLastScanned(a) ? 1 : -1));
        },
    },
    computed: {
        all_lines_done: function() {
            return this.products.every(prod => prod.done);
        },
        no_products: function() {
            return this.products.every(prod => prod.qty_done === 0);
        },
        formatedProducts: function() {
            return this.formatProduct(this.products);
        },
        multipleLocation: function() {
            return !this.products.every(p => p.location_src.id === this.products[0].location_src.id);
        },
        productByLocation: function() {
            let locations = this.products.map(p => p.location_src);
            locations = locations.filter((p, i) => locations.findIndex(loc => loc.id === p.id) === i);

            locations.forEach((location) => {
                location.products = this.formatProduct(this.products.filter(prod => prod.location_src.id === location.id));
            });
            locations.sort((a, b) => a.products.reduce((acc, p) => acc = p.id === this.lastScanned) ? 1 : -1);

            return locations;
        },
    },
    template: `
    <v-container class="mb-16">
        <detail-picking
            :record="packing"
        />
        <detail-simple-product
            v-for="product in formatedProducts"
            v-if="!multipleLocation"
            :product="product"
            :fields="fields"
            :key="product.id"
            :selected="isLastScanned(product)"
            />
        <div v-if="multipleLocation" v-for="location in productByLocation">
            <item-detail-card
                :record="location"
                />
            <detail-simple-product
                v-for="product in location.products"
                :product="product"
                :fields="fields"
                :key="product.id"
                :selected="isLastScanned(product)"
                />
        </div>
        </div>
        <div style="position: fixed; bottom: 0; right: 12px;width: 100%">
            <v-row>
                <v-col
                    class="d-flex justify-end"
                    >
                    <v-btn
                        x-large
                        class="justify-end"
                        @click="$emit('skipPack')"
                        :color="utils.colors.color_for('accent')">
                        Skip
                    </v-btn>
                    <v-btn
                        v-if="all_lines_done"
                        x-large
                        class="justify-end"
                        @click="$emit('shippedFinished')"
                        :color="utils.colors.color_for('screen_step_done')"
                        style="margin-left: 12px;"
                        >
                        Package done
                    </v-btn>
                    <v-btn
                        v-if="!all_lines_done && !no_products"
                        x-large
                        @click="$emit('shippedUnfinished')"
                        style="margin-left: 12px;"
                        :color="utils.colors.color_for('secondary')">
                        Ship unfinished
                    </v-btn>
                </v-col>
            </v-row>
        </div>
    </v-container>
`,
});
