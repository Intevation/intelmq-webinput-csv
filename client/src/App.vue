<template>
  <div id="app">
    <WebinputCSV />
  </div>
</template>

<script>
import WebinputCSV from './components/WebinputCSV.vue'

export default {
  name: 'App',
  components: {
    WebinputCSV
  },
  mounted () {
    this.$store.dispatch('login', {
        username: '',
        password: ''
    }).then(() => {
        this.$store.commit("HAS_AUTH", false);
        this.$store.dispatch("fetchClassificationTypes");
        this.$store.dispatch("fetchHarmonizationFields");
        this.$store.dispatch("fetchCustomFields");
    })
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}
.v-leave-active {
  transition: opacity 2s ease;
}
.v-leave-to {
  opacity: 0;
}
</style>
