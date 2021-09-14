<template>
  <div>
    <b-navbar toggleable="lg" type="dark" variant="info">
      <b-navbar-brand href="#">IntelMQ - Webinput CSV</b-navbar-brand>
      <b-navbar-nav v-if="hasAuth" class="ml-auto">
        <b-button v-if="!loggedIn" v-b-modal.login-popup size="sm" class="my-2 my-sm-0" type="submit">Login</b-button>
        <b-button v-if="loggedIn" size="sm" class="my-2 my-sm-0" @click="signOut">Logout</b-button>
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
      <div class="accordion" role="tablist">
        <b-card no-body class="mb-1">
          <b-card-header header-tag="header" class="p-1" role="tab">
            <b-button block v-b-toggle.accordion-1 variant="info">CSV Content</b-button>
          </b-card-header>
          <b-collapse id="accordion-1" visible accordion="my-accordion" role="tabpanel">
            <b-card-body>
              <b-form-group >
                <b-form-file
                  v-model="csvFile"
                  placeholder="Choose a file or drop it here..."
                  drop-placeholder="Drop file here..."
                ></b-form-file>
              </b-form-group>
              <b-form-group >
                <b-form-textarea
                  id="textarea"
                  v-model="csvData"
                  placeholder="Or paste CSV data here"
                  rows="5"
                ></b-form-textarea>
              </b-form-group>
              <b-container fluid>
                <b-row>
                  <b-col>
                    <b-form-group label-cols=4 label="Delimiter">
                      <b-form-select v-model="delimiter" :options="delimiterOptions"></b-form-select>
                    </b-form-group>
                  </b-col>
                  <b-col>
                    <b-form-group label-cols=4 label="Quote char">
                      <b-form-input v-model="quoteChar" type="text" placeholder='"'></b-form-input>
                    </b-form-group>
                  </b-col>
                  <b-col>
                    <b-form-group label-cols=4 label="Escape char">
                      <b-form-input v-model="escapeChar" type="text" placeholder="\"></b-form-input>
                    </b-form-group>
                  </b-col>
                  <b-col>
                    <b-form-group label-cols=4 label="Has Header">
                      <b-form-checkbox v-model="hasHeader"></b-form-checkbox>
                    </b-form-group>
                  </b-col>
                </b-row>
              </b-container>
            </b-card-body>
          </b-collapse>
        </b-card>

        <b-card no-body class="mb-1">
          <b-card-header header-tag="header" class="p-1" role="tab">
            <b-button :disabled="!csvFile && csvData === ''" block v-b-toggle.accordion-2 variant="info">Options</b-button>
          </b-card-header>
          <b-collapse id="accordion-2" accordion="my-accordion" role="tabpanel">
            <b-card-body>
              <b-container fluid>
                <b-row>
                  <b-col>
                    <b-form-group id="option1" label-cols=7 label="Skip initial Whitespace">
                      <b-form-checkbox v-model="initialWhitespace"></b-form-checkbox>
                    </b-form-group>
                    <b-tooltip target="option1" triggers="hover">
                      When True, whitespace immediately following the delimiter is ignored.
                    </b-tooltip>
                  </b-col>
                  <b-col>
                    <b-form-group id="option2" label-cols=7 label="Skip initial N lines">
                      <b-form-input v-model="skipLines" type="number"></b-form-input>
                    </b-form-group>
                    <b-tooltip target="option2" triggers="hover">
                      Skip initial N lines after the header.
                    </b-tooltip>
                  </b-col>
                  <b-col>
                    <b-form-group id="option3" label-cols=7 label="Show N lines maximum in preview">
                      <b-form-input v-model="maxPreview" type="number"></b-form-input>
                    </b-form-group>
                    <b-tooltip target="option3" triggers="hover">
                      Do not show more than N lines in the preview. All the data is processed by the backend.
                    </b-tooltip>
                  </b-col>
                </b-row>
              </b-container>
            </b-card-body>
          </b-collapse>
        </b-card>

        <b-card no-body class="mb-1">
          <b-card-header header-tag="header" class="p-1" role="tab">
            <b-button :disabled="!csvFile && csvData === ''" block v-b-toggle.accordion-3 variant="info">Preview</b-button>
          </b-card-header>
          <b-collapse id="accordion-3" accordion="my-accordion" role="tabpanel">
            <b-card-body>
              <b-card-text>{{ text }}</b-card-text>
            </b-card-body>
          </b-collapse>
        </b-card>
      </div>
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
      wrongCredentials: false,
      csvFile: null,
      csvData: "",
      delimiter: ";",
      delimiterOptions: [
        {value: ";", text: ";"},
        {value: ",", text: ","},
        {value: "#", text: "#"}
      ],
      quoteChar: '"',
      escapeChar: "\\",
      hasHeader: false,
      initialWhitespace: false,
      skipLines: 0,
      maxPreview: 0
    }
  },
  computed: {
    ...mapState(['user', 'loggedIn', 'hasAuth']),
  },
  mounted() {
  },
  methods: {
    signIn: function () {
      this.$store.dispatch("login", {
        username: this.username,
        password: this.password
      }).then(() => {
        this.wrongCredentials = false
        this.$bvModal.hide("login-popup")
        this.$store.dispatch("fetchClassificationTypes");
        this.$store.dispatch("fetchHarmonizationFields");
      }, () => {
          this.wrongCredentials = true
      })
    },
    signOut: function () {
      this.username = ''
      this.password = ''
      this.wrongCredentials = false
      this.$store.dispatch("logout")
    },  
  }
})
</script>
