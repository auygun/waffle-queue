import 'material-icons/iconfont/filled.css';
import './assets/custom-simple.css'
// import './assets/custom-water.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Axios from 'axios';
import { setupCache, type AxiosCacheInstance } from 'axios-cache-interceptor';

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

const axiosInstance = setupCache(Axios.create())
export const useAxios: () => AxiosCacheInstance = () => axiosInstance

app.mount('#app')
