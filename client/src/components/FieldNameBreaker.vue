<template>
  <span
    style="overflow-wrap: break-word;"
  ><span
    v-for="(part, i) in parts"
    :key="i"
  >{{ part }}<wbr/></span></span>
</template>

<script>
export default ({
  name: 'FieldNameBreaker',
  props: {
    fieldName: {
      type: String,
      default: () => ''
    }
  },
  computed: {
    parts() {
      let s = this.fieldName;
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
    }
  }
})
</script>
