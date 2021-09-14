import '@babel/polyfill'
import 'mutationobserver-shim'
import Vue from 'vue'
import Resource from 'vue-resource'
import './plugins/bootstrap-vue'
import App from './App.vue'
import store from './store'

Vue.config.productionTip = false

Vue.use(Resource);

Vue.http.interceptors.push((request, next) => {
  var headers = request.headers
  console.log(request);
  if (request.url !== 'api/login'
    && !Object.prototype.hasOwnProperty.call(headers, 'Authorization')
  ) {
    headers.map.Authorization = [store.state.token]
  }
  console.log(headers)

  // continue to next interceptor without modifying the response
  next()
})

new Vue({
  store,
  render: h => h(App)
}).$mount('#app')
