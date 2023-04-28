import '@babel/polyfill'
import 'mutationobserver-shim'
import Vue from 'vue'
import vSelect from 'vue-select'
import "vue-select/dist/vue-select.css";
import Resource from 'vue-resource'
import './plugins/bootstrap-vue'
import App from './App.vue'
import store from './store'

Vue.config.productionTip = false

Vue.use(Resource);
Vue.component("v-select", vSelect);

Vue.http.interceptors.push((request, next) => {
  var headers = request.headers
  if (request.url !== 'api/login'
    && !Object.prototype.hasOwnProperty.call(headers, 'Authorization')
  ) {
    headers.map.Authorization = [store.state.token]
  }
  // continue to next interceptor without modifying the response
  next()
})

new Vue({
  store,
  render: h => h(App)
}).$mount('#app')
