/* eslint-disable strict */
/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("searchbar", {
    data: function () {
        return {
            entered: "",
            autofocus: {
                type: Boolean,
                default: true,
            },
        };
    },
    props: {
        input_placeholder: String,
        input_data_type: String,
        reset_on_submit: {
            type: Boolean,
            default: true,
        },
        refocusInput: Boolean,
    },
    methods: {
        search: function (e) {
            e.preventDefault();
            // Talk to parent
            this.$emit("found", {
                text: this.entered,
                type: e.target.dataset.type,
            });
            if (this.reset_on_submit) this.reset();
        },
        reset: function () {
            this.entered = "";
        },
        on_screen_reload: function(evt) {
            if (this.reload_steal_focus) this.$refs.input.focus();
        },
        refocus: function() {
            if (this.refocusInput) {
                setTimeout(() => this.$refs.input.focus());
            }
        },
    },

    template: `
  <v-form
      v-on:submit="search"
      :data-type="input_data_type"
      ref="form"
      class="searchform"
      >
    <v-text-field
      name="searchbar"
      ref="input"
      required v-model="entered"
      :placeholder="input_placeholder"
      :autofocus="autofocus ? 'autofocus' : null"
      :autocomplete="autocomplete"
      @blur="refocus()"
      />
  </v-form>
  `,
});
