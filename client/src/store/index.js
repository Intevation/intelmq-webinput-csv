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
    classificationTypeMapping: [],
    harmonizationFields: [],
    harmonizationFieldMapping: [],
    customFields: [],
    customFieldsMapping: [],
    requiredFields: [],
    mailgenAvailable: null,
    botsAvailable: {status: false, reason: "not yet queried"},
    mailgenAvailableTargetGroups: []
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
    SET_TYPE_MAPPING (state, data) {
      state.classificationTypeMapping = data;
    },
    SET_FIELDS (state, data) {
      state.harmonizationFields = data;
    },
    SET_FIELD_MAPPING (state, data) {
      state.harmonizationFieldMapping = data;
    },
    HAS_AUTH (state, hasAuth) {
      state.hasAuth = hasAuth;
    },
    SET_CUSTOM_FIELDS (state, data) {
      state.customFields = data;
    },
    SET_CUSTOM_FIELDS_MAPPING (state, data) {
      state.customFieldsMapping = data;
    },
    SET_REQUIRED_FIELDS (state, data) {
      state.requiredFields = data;
    },
    SET_MAILGEN_AVAILABLE (state, data) {
      state.mailgenAvailable = data;
    },
    SET_BOTS_AVAILABLE (state, data) {
      state.botsAvailable = data;
    },
    SET_MAILGEN_AVAILABLE_TARGET_GROUPS(state, data) {
      state.mailgenAvailableTargetGroups = data;
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
              reject(response);
            }
          }), (response) => reject(response)
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
            context.commit("SET_TYPES", Object.keys(data));
            context.commit("SET_TYPE_MAPPING", data);
          }
        })
      )
    },
    fetchHarmonizationFields(context) {
      Vue.http.get("api/harmonization/event/fields").then(
        response => response.json().then(data => {
          if (data) {
            context.commit("SET_FIELDS", Object.keys(data));
            context.commit("SET_FIELD_MAPPING", data);
          }
        })
      )
    },
    fetchCustomFields(context) {
      Vue.http.get("api/custom/fields").then(
        response => response.json().then(data => {
          if (data) {
            context.commit("SET_CUSTOM_FIELDS", data);
            let keys = Object.keys(data);
            let mapping = [];
            for (let key of keys) {
              mapping.push({
                key: key,
                value: data[key]
              })
            }
            context.commit("SET_CUSTOM_FIELDS_MAPPING", mapping)
          }
        })
      )
    },
    fetchRequiredFields(context) {
      Vue.http.get("api/custom/required_fields").then(
        response => response.json().then(data => {
          if (data) {
            context.commit("SET_REQUIRED_FIELDS", data);
          }
        })
      )
    },
    fetchMailgenAvailable(context) {
      Vue.http.get("api/mailgen/available").then(
        response => response.json().then(data => {
          context.commit("SET_MAILGEN_AVAILABLE", data);
        })
      )
    },
    fetchBotsAvailable(context) {
      Vue.http.get("api/bots/available").then(
        response => response.json().then(data => {
          context.commit("SET_BOTS_AVAILABLE", data);
        })
      )
    },
    fetchMailgenAvailableTargetGroups(context) {
      Vue.http.get("api/mailgen/target_groups").then(
        response => {
          response.json().then(data => {
            if (typeof data == "object") {
              context.commit("SET_MAILGEN_AVAILABLE_TARGET_GROUPS", data)
            } else {
              console.error('WEBINPUT: fetch target groups, not an object:', data)
            }
        }).catch(err => { // not json
          console.error('WEBINPUT: fetch target groups, not json, err:', err)
        });

        }, (response) => { // error
          console.error('WEBINPUT: fetch target groups, response error:', response)
        }
        )
    }
  },
  modules: {
  }
})
