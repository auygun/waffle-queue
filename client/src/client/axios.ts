import Axios, { AxiosError, type AxiosRequestConfig } from 'axios'

const axiosInstance = Axios.create()

export const useAxios = () => {
  function getBaseUrl(): string | undefined {
    return 'http://127.0.0.1:5001'
  }

  async function get(url: string, params = {}) {
    const config: AxiosRequestConfig = {
      params: params,
      headers: { 'Content-Type': 'application/json' },
    }
    return await axiosInstance.get(url, config)
  }

  async function postFormData(url: string, formData: FormData, params = {}) {
    const config: AxiosRequestConfig = {
      params: params,
      headers: { 'Content-Type': 'multipart/form-data' },
    }
    return await axiosInstance.post(url, formData, config)
  }

  async function postText(url: string, data: string, params = {}) {
    const config: AxiosRequestConfig = {
      params: params,
      headers: { 'Content-Type': 'text/plain' },
    }
    return await axiosInstance.post(url, data, config)
  }

  return {
    getBaseUrl,
    get,
    postFormData,
    postText,
  }
}

export function AxiosErrorToString(error: AxiosError<string>): [string, string] {
  return [error.response?.status + ' (' + error.response?.statusText + ')', error.response?.data ?? '']
}
