<template>
<div v-show="items.length > 0">
  <ul style="display: grid; grid-auto-flow: row; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 5px; margin: 0; padding: 0; border: none;">
    <li
      v-for="(el, i) in items"
      :key="i"
      style="display: block; margin: 0; padding: 0; border: none;"
    ><b-button
      variant="outline-secondary"
      @click="$emit('click', el)"
    ><field-name-breaker
      :field-name="el"
    /></b-button></li>
  </ul>
</div>
</template>

<script>
import fieldNameBreaker from './FieldNameBreaker.vue';

export default ({
  name: 'FieldNameButtonList',
  props: {
    items: {
      type: Array,
      default: () => []
    }
  },
  components: {fieldNameBreaker}
})
</script>
