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
    customFields: [],
    customFieldsMapping: [],
    requiredFields: [],
    mailgenAvailable: null,
    botsAvailable: {status: false, reason: "not yet queried"},
    mailgenAvailableTargetGroups: [],
    mailgenAvailableTargetGroupsStatus: null,
    backendVersion: null,
    // the templates in the client. The client only modifies them and is able to compare them with the
    mailgenTemplates: [],
    // the templates on the server
    mailgenTemplatesServer: [],
    mailgenMultiTemplatesEnabled: false,
    mailgenTemplateDefaultTemplateName: null,
    customWorkflowDefault: false,
    allowValidationOverride: true
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
    },
    SET_BACKEND_VERSION(state, data) {
      state.backendVersion = data;
    },
    SET_MAILGEN_AVAILABLE_TARGET_GROUPS_STATUS(state, data) {
      state.mailgenAvailableTargetGroupsStatus = data;
    },
    SET_TEMPLATES(state, data) {
      state.mailgenTemplates = data;
      // create a deep clone, otherwise both names have the same reference. deep clone is required as the list items are objects themselves
      state.mailgenTemplatesServer = JSON.parse(JSON.stringify(data));
    },
    SET_MAILGEN_MULTI_TEMPLATES_ENABLED(state, data) {
      state.mailgenMultiTemplatesEnabled = data;
    },
    SET_MAILGEN_DEFAULT_TEMPLATE_NAME(state, data) {
      state.mailgenTemplateDefaultTemplateName = data;
    },
    SET_SETTNGS(state, data) {
      state.customWorkflowDefault = data['custom_workflow_default'];
      state.allowValidationOverride = data['allow_validation_override'];
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
            // construct the object expected by b-form-select: https://bootstrap-vue.org/docs/components/form-select#form-select
            let groupedTypes = Object();
            for (let [type, taxonomy] of Object.entries(data)) {
              if (!(taxonomy in groupedTypes)) {
                groupedTypes[taxonomy] = []
              }
              groupedTypes[taxonomy].push(type)
            }
            let typeInputOptions
            let typeOptions = []
            for (let taxonomy of Object.keys(groupedTypes)) {
              typeInputOptions = []
              groupedTypes[taxonomy].sort()  // is in-place sorting
              for (let type of groupedTypes[taxonomy]) {
                typeInputOptions.push({value: type, text: type})
              }
              typeOptions.push({
                label: taxonomy,
                options: typeInputOptions
              })
            }
            context.commit("SET_TYPES", typeOptions);
            context.commit("SET_TYPE_MAPPING", data);
          }
        })
      )
    },
    fetchHarmonizationFields(context) {
      Vue.http.get("api/harmonization/event/fields").then(
        response => response.json().then(data => {
          if (data) {
            context.commit("SET_FIELDS", data);
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
              context.commit("SET_MAILGEN_AVAILABLE_TARGET_GROUPS_STATUS", true)
              context.commit("SET_MAILGEN_AVAILABLE_TARGET_GROUPS", data)
            } else {
              context.commit("SET_MAILGEN_AVAILABLE_TARGET_GROUPS_STATUS", data)
            }
        }).catch(err => { // not json
          context.commit("SET_MAILGEN_AVAILABLE_TARGET_GROUPS_STATUS", err)
        });

        }, (response) => { // error
          context.commit("SET_MAILGEN_AVAILABLE_TARGET_GROUPS_STATUS", "Status: " + response.status + " (" + response.statusText + ") Body: " + response.body)
        }
        )
    },
    fetchBackendVersion(context) {
      Vue.http.get("api/version").then(
        response => {
          response.json().then(data => {
            context.commit("SET_BACKEND_VERSION", data)
            })
        });
    },
    fetchMailgenTemplates(context) {
      Vue.http.get('api/mailgen/templates').then(
        response => {
          response.json().then(data => {
            let template_names = Object.keys(data);
            let mapping = [];
            for (let key of template_names) {
              mapping.push({
                name: key,
                body: data[key],
                validationStatus: null,
                validationText: ''
              });
            }
            if (template_names.length == 0) {
              // create an empty template to start with
              mapping = [{'name': '', 'body': ''}];
            }
            context.commit("SET_TEMPLATES", mapping)
          })
        }
      );

      Vue.http.get("api/mailgen/settings").then(
        response => response.json().then(data => {
          context.commit("SET_MAILGEN_MULTI_TEMPLATES_ENABLED", data['multi_templates_enabled']);
          context.commit("SET_MAILGEN_DEFAULT_TEMPLATE_NAME", data['default_template_name']);
        })
      );
    },
    fetchSettings(context) {
      Vue.http.get('api/settings').then(
        response => {
          response.json().then(data => {
            context.commit("SET_SETTNGS", data)
          })
        }
      )
    }
  },
  modules: {
  }
})
