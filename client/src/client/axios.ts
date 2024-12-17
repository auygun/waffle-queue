// import { useAuthStore } from '@/store/authStore'
import Axios, { type AxiosRequestConfig } from 'axios'
import {
  setupCache,
  type AxiosCacheInstance,
  type CacheAxiosResponse,
} from 'axios-cache-interceptor'

const axiosInstance = createAxiosInstance()

export const useAxios = () => {
  function getBaseUrl(): string | undefined {
    return axiosInstance.defaults.baseURL
  }

  function get(url: string, params = {}) {
    return axiosInstance.get(url, paramsToAxiosRequestConfig(params))
  }

  function postFormData(
    url: string,
    formData: FormData,
    params = {},
  ): Promise<CacheAxiosResponse<any, any>> {
    const config = paramsToAxiosRequestConfig(params)
    config.headers = { 'Content-Type': 'multipart/form-data' }
    return axiosInstance.post(url, formData, config)
  }

  function postText(url: string, data: string, params = {}) {
    const config = paramsToAxiosRequestConfig(params)
    config.headers = { 'Content-Type': 'text/plain' }
    return axiosInstance.post(url, data, config)
  }

  function setCredentials(
    username: string,
    password: string,
    onAuthenticatedUpdated: (authenticated: boolean) => void,
  ) {
    axiosInstance.defaults.auth = {
      username: username,
      password: password,
    }
    // useAuthStore().updateAuthenticated((authenticated) => {
    //   onAuthenticatedUpdated(authenticated)
    // })
  }

  function paramsToAxiosRequestConfig(params: any): AxiosRequestConfig {
    return {
      params: params,
    }
  }

  return {
    getBaseUrl,
    get,
    postFormData,
    postText,
    setCredentials,
  }
}

function createAxiosInstance(): AxiosCacheInstance {
  const axiosInstance = setupCache(Axios.create())

  // Request interceptor
  axiosInstance.interceptors.request.use((config) => {
    config.headers.setAccept('application/json')
    if (!config.headers.getContentType()) {
      config.headers.setContentType('application/json')
    }
    config.withCredentials = true

    if (axiosInstance.defaults.auth) {
      config.auth = axiosInstance.defaults.auth
    }
    return config
  })

  // Response interceptor
  axiosInstance.interceptors.response.use(
    (response) => {
      return response
    },
    (error) => {
      // if (error.status === 401) useAuthStore().setAuthenticated(false)
      console.error(error)
      return Promise.reject(error)
    },
  )

  return axiosInstance
}
