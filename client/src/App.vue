<template>
  <div id="app">
    <Main />
  </div>
</template>

<script>
import Main from './components/Main.vue'

export default {
  name: 'App',
  components: {
    Main
  },
  mounted () {
    this.$http.post('login', {
      username: '',
      password: ''
    }).then(response => response.json().then(data => {
      if (data && data.login_token === null) {
        this.$store.state.loggedIn = true
        this.$store.state.user = ''
      }
    }))
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
</style>
