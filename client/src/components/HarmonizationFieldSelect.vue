<template>
  <div>
    <div
      style="cursor: pointer; margin-bottom: 4px; overflow-wrap: break-word;"
      @click="$refs.modal.show()"
    ><span
      v-for="(part, i) in valueParts"
      :key="i"
    >{{ part }}<wbr/></span></div>
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
      :ok-disabled="!sanitizedModalValue"
      @hide="onModalHide"
    >
      <div>
        <b-form @submit="onModalFormSubmit">
          <b-form-input
            type="text"
            v-model="modalValue"
            placeholder="Field"
            autofocus
          />
        </b-form>
        TODO
      </div>
    </b-modal>
  </div>
</template>

<script>
// Documentation on b-modal:
// https://bootstrap-vue.org/docs/components/modal/

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
    }
  },
  model: {
    prop: 'value',
    event: 'update'
  },
  data() {
    return {
      modalValue: ''
    };
  },
  computed: {
    valueParts() {
      let s = this.value;
      let r = [];
      while (s) {
        const m = /^(?:[a-z]+|[0-9]+)/i.exec(s);
        if (!m) {
          r.push(s[0]);
          s = s.substring(1);
          continue;
        }
        const text = m[0];
        r.push(text);
        s = s.substring(text.length);
      }
      return r;
    },
    sanitizedModalValue() {
      // Most sanitization is done in WebinputCSV.vue
      return this.modalValue.trim();
    }
  },
  methods: {
    update(newValue) {
      this.$emit('update', newValue);
    },
    onModalHide(e) {
      if (e.trigger === 'ok') this.update(this.sanitizedModalValue);
      this.modalValue = '';
    },
    onModalFormSubmit(e) {
      e.preventDefault();
      if (!this.sanitizedModalValue) return;
      this.$refs.modal.hide('ok');
    }
  }
})
</script>
