import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    user: null,
    token: null,
    loggedIn: false,
    hasAuth: true,
    classificationTypes: [],
    harmonizationFields: []
  },
  mutations: {
    SET_USER (state, user) {
      state.user = user
    },
    SET_TOKEN (state, token) {
      state.token = token
    },
    SET_LOGGED_IN (state, loggedIn) {
      state.loggedIn = loggedIn
    },
    SET_TYPES (state, data) {
      state.classificationTypes = data;
    },
    SET_FIELDS (state, data) {
      state.harmonizationFields = data;
    },
    HAS_AUTH (state, hasAuth) {
      state.hasAuth = hasAuth;
    }
  },
  actions: {
    login(context, credentials) {
      return new Promise((resolve, reject) => {
        Vue.http.post('api/login', credentials).then(
          response => response.json().then(data => {
            if (data
              && data.login_token !== null
              && data.login_token !== undefined
              && data.username !== undefined && data.username !== ''
            ) {
              context.commit("SET_USER", data.username);
              context.commit("SET_TOKEN", data.login_token);
              context.commit("SET_LOGGED_IN", true);
              resolve();
            } else {
              reject();
            }
          })
        )
      })
    },
    logout(context) {
      context.commit("SET_USER", null);
      context.commit("SET_TOKEN", null);
      context.commit("SET_LOGGED_IN", false);
    },
    fetchClassificationTypes(context) {
      Vue.http.get("api/classification/types").then(
        response => response.json().then(data => {
          if (data) {
            context.commit("SET_TYPES", data);
          }
        })
      )
    },
    fetchHarmonizationFields(context) {
      Vue.http.get("/api/harmonization/event/fields").then(
        response => response.json().then(data => {
          if (data) {
            context.commit("SET_FIELDS", data);
          }
        })
      )
    }
  },
  modules: {
  }
})
