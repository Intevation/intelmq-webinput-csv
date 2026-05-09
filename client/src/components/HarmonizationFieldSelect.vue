<template>
  <div>
    <div
      style="cursor: pointer; margin-bottom: 4px;"
      @click="$refs.modal.show()"
    ><field-name-breaker
      :field-name="value"
    /></div>
    <div style="display: flex; flex-direction: row; flex-wrap: wrap; justify-content: center; align-items: center; row-gap: 4px;">
      <div style="padding: 0 3px;"><b-button
        size="sm"
        variant="outline-dark"
        @click="$refs.modal.show()"
      >📝</b-button></div>
      <div style="padding: 0 3px;"><b-button
        size="sm"
        variant="outline-dark"
        :disabled="!value"
        @click="update('')"
      >❌</b-button></div>
    </div>
    <b-modal
      ref="modal"
      size="xl"
      centered
      scrollable
      hide-footer
      content-class="full-height"
      @hide="onModalHide"
    >
      <template #modal-header="{ ok, cancel }">
        <div style="display: flex; flex-direction: column; row-gap: 10px; width: 100%;">
          <b-form @submit.prevent="sanitizedModalValue && ok()">
            <b-form-input
              type="text"
              v-model="modalValue"
              placeholder="Field"
              autofocus
            />
          </b-form>
          <div style="display: flex; flex-direction: row; justify-content: end; column-gap: 8px;">
            <div><b-button
              variant="secondary"
              @click="cancel()"
            >Cancel</b-button></div>
            <div><b-button
              variant="primary"
              :disabled="!sanitizedModalValue"
              @click="ok()"
            >OK</b-button></div>
          </div>
        </div>
      </template>
      <template #default="{ ok }">
        <div>
          <div v-if="options.length > 0">
            <div v-show="!sanitizedModalValue">
              <div v-show="suggestions.length > 0" style="margin-bottom: 6px;">
                <h3 style="margin: 0; padding: 0; margin-bottom: 3px;">Suggested</h3>
                <field-name-button-list
                  :items="suggestions"
                  @click="modalValue = $event, ok()"
                />
              </div>
              <div>
                <h3 style="margin: 0; padding: 0; margin-bottom: 3px;">All</h3>
                <field-name-button-list
                  :items="options"
                  @click="modalValue = $event, ok()"
                />
              </div>
            </div>
            <div v-show="sanitizedModalValue">
              <h3 style="margin: 0; padding: 0; margin-bottom: 3px;">Results</h3>
              <field-name-button-list
                :items="searchResults"
                @click="modalValue = $event, ok()"
              />
              <div v-show="searchResults.length === 0"><i>No results.</i></div>
            </div>
          </div>
          <div v-else><i>No suggestions available.</i></div>
        </div>
      </template>
    </b-modal>
  </div>
</template>

<style>
.full-height {
  height: 100% !important;
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  box-sizing: border-box !important;
}
</style>

<script>
// Documentation on b-modal:
// https://bootstrap-vue.org/docs/components/modal/

import fieldNameBreaker from './FieldNameBreaker.vue';
import fieldNameButtonList from './FieldNameButtonList.vue';

export default ({
  name: 'HarmonizationFieldSelect',
  props: {
    value: {
      type: String,
      default: () => ''
    },
    options: {
      type: Array,
      default: () => []
    },
    candidateInfo: {
      type: Object,
      default: () => ({})
    }
  },
  model: {
    prop: 'value',
    event: 'update'
  },
  components: {fieldNameBreaker, fieldNameButtonList},
  data() {
    return {
      modalValue: ''
    };
  },
  computed: {
    sanitizedModalValue() {
      // Most sanitization is done in WebinputCSV.vue
      return this.modalValue.trim();
    },
    possibleIpSuggestions() {
      return [
        'destination.ip',
        'destination.local_ip',
        'source.ip',
        'source.local_ip'
      ].filter(el => this.options.includes(el));
    },
    possibleDatetimeSuggestions() {
      return [
        'destination.allocated',
        'source.allocated',
        'time.observation',
        'time.source'
      ].filter(el => this.options.includes(el));
    },
    suggestions() {
      return (this.candidateInfo['ip'] ? this.possibleIpSuggestions : []).concat(this.candidateInfo['timestamp'] ? this.possibleDatetimeSuggestions : []);
    },
    searchPattern() {
      const s = this.sanitizedModalValue;
      if (!s) return /^(?!)/; // Never matches
      const se = RegExp.escape(s);
      if (/^[\W_]/.test(s)) return RegExp(se, 'i');
      return RegExp(`\\b${se}`, 'i');
    },
    searchResults() {
      return this.options.filter(el => this.searchPattern.test(el));
    }
  },
  methods: {
    update(newValue) {
      this.$emit('update', newValue);
    },
    onModalHide(e) {
      if (e.trigger === 'ok') this.update(this.sanitizedModalValue);
      this.modalValue = '';
    }
  }
})
</script>
