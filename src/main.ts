import 'material-icons/iconfont/filled.css';
import './assets/custom-simple.css'
// import './assets/custom-water.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.config.globalProperties.$axios = axios

app.mount('#app')
