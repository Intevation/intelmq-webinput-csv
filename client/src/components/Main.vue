<template>
  <div>
    <b-navbar toggleable="lg" type="dark" variant="info">
      <b-navbar-brand href="#">IntelMQ - Webinput CSV</b-navbar-brand>
      <b-navbar-nav class="ml-auto">
	<b-button v-b-modal.login-popup size="sm" class="my-2 my-sm-0" type="submit">Login</b-button>
      </b-navbar-nav>
    </b-navbar>
    <div>
      <b-modal v-model="showLogin" id="login-popup" title="IntelMQ - Webinput-CSV - Sign in">
        <label v-if="wrongCredentials" class="text-danger">Wrong username or password</label>
	<b-form>
	<div>
        <label for="username">Username</label>
        <b-form-input v-model="username" type="text" id="username"  placeholder="Name"></b-form-input>
        <label for="password">Password</label>
        <b-form-input v-model="password" type="password" id="password"  placeholder="Password"></b-form-input>
	</div>
	</b-form>
        <template #modal-footer>
            <b-button
              variant="primary"
              size="sm"
              class="float-right"
              @click="signIn"
            >
              Login
            </b-button>
        </template>   
      </b-modal>
    </div>
    <div v-if="loggedIn">
      <label>Logged in!</label>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex';
export default ({
  data: () => {
    return {
      username: "",
      password: "",
      showLogin: false,
      wrongCredentials: false 
    }
  },
  computed: {
    ...mapState(['user', 'loggedIn']),
  },
  mounted() {
	
  },
  methods: {
    signIn: function () {
      fetch('api/login', {
	method: "POST",
	headers: {
          "Content-Type": "application/json"
	},
	body: JSON.stringify({
          username: this.username,
          password: this.password
	})
      }).then(response => response.json().then(data => {
        if (data && data.login_token !== null && data.login_token !== undefined && data.username !== undefined && data.username !== '') {
          this.$store.state.user = data.username
          this.$store.state.token = data.login_token
          this.$store.state.loggedIn = true
          this.wrongCredentials = false
	  this.$bvModal.hide("login-popup")
        } else {
          this.wrongCredentials = true
        }
      }))
    },
    signOut: function () {
      this.username = ''
      this.password = ''
      this.wrongCredentials = false
      this.$store.state.token = null
      this.$store.state.user = null
      this.$store.state.loggedIn = false
    },  
  }
})
</script>
