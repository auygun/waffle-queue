<script setup lang="ts">
import { AxiosErrorToString, useAxios } from '@/client/axios'
import { computed, type ComputedRef, ref, type Ref, watch } from 'vue'
import router from '@/router'
import Paginator from '@/components/Paginator.vue'
import type { AxiosError } from 'axios'

const LAST_QUEUE_VIEW_RECORDS_PER_PAGE = "LastQueueViewRecordsPerPage"

type Request = {
  id: number
  project: string
  integration: boolean
  source_branch: string
  target_branch: string
  state: string
}

type Build = {
  id: number
  request_id: number
  worker_id: number
  build_config: string
  remote_url: string
  source_branch: string
  build_script: string
  state: string
}

type Row = {
  request: Request | undefined
  builds: Build[]
  isDetail: boolean
  expanded: boolean
  bgColor: string
}

const props = defineProps({
  offset: {
    type: String,
    default: '0',
  },
})

const emit = defineEmits<{
  toastEvent: [message: [string, string]]
}>()

const rows: Ref<Row[]> = ref([])

const requests: Ref<Request[]> = ref([])

const totalRecords: Ref<number> = ref(0)
const recordsPerPage: Ref<number> = ref(getRecordsPerPage(5))
const loading: Ref<boolean> = ref(false)
const syncError: Ref<boolean> = ref(false)
const page: Ref<number> = ref(getPageForOffset())

watch(page,
  () => {
    router.replace({ query: { offset: getOffsetForPage().toString() } })
  }
)

watch(() => props.offset,
  async () => {
    page.value = getPageForOffset()
    await updateBuildQueue()
  },
  { immediate: true }
)

watch(recordsPerPage,
  async (newValue) => {
    localStorage.setItem(LAST_QUEUE_VIEW_RECORDS_PER_PAGE, newValue.toString())
    await updateBuildQueue()
  }
)

function getOffsetForPage(): number {
  return (page.value - 1) * recordsPerPage.value
}

function getPageForOffset(): number {
  return Math.floor(Number(props.offset) / recordsPerPage.value) + 1
}

function getRecordsPerPage(defaultValue: number): number {
  try {
    const cachedValue = localStorage.getItem(LAST_QUEUE_VIEW_RECORDS_PER_PAGE)
    return cachedValue ? Number(cachedValue) : defaultValue
  } catch { return defaultValue }
}

async function updateBuildQueue() {
  loading.value = true
  syncError.value = false
  try {
    const response = await useAxios().get('/api/v1/requests', {
      offset: Number(props.offset),
      limit: recordsPerPage.value,
    })
    totalRecords.value = response.data.count
    requests.value = response.data.content

    // Add or remove rows depending on number requests we have
    if (rows.value.length < requests.value.length * 2) {
      for (let i = rows.value.length / 2; i < requests.value.length; ++i) {
        const color = i % 2 !== 0 ? "var(--accent-bg)" : "var(--bg)"
        rows.value.push({ request: undefined, builds: [], isDetail: false, expanded: false, bgColor: color })
        rows.value.push({ request: undefined, builds: [], isDetail: true, expanded: false, bgColor: color })
      }
    } else if (rows.value.length > requests.value.length * 2) {
      for (let i = requests.value.length * 2; i < rows.value.length; ++i) {
        rows.value.pop()
        rows.value.pop()
      }
    }

    // Fill up rows with data
    for (let i = 0; i < requests.value.length; ++i) {
      let builds: Build[] = []
      try {
        const response = await useAxios().get(`/api/v1/builds/${requests.value[i].id}`)
        builds = response.data.content
      } catch (error) {
        syncError.value = true
        emit('toastEvent', AxiosErrorToString(error as AxiosError<string>))
      } finally {
        loading.value = false
      }
      rows.value[i * 2].request = rows.value[(i * 2) + 1].request = requests.value[i]
      rows.value[i * 2].builds = rows.value[(i * 2) + 1].builds = builds
    }
  } catch (error) {
    syncError.value = true
    emit('toastEvent', AxiosErrorToString(error as AxiosError<string>))
  } finally {
    loading.value = false
  }
}

async function abort(request_id: number) {
  try {
    const formData = new FormData()
    await useAxios().postFormData(`/api/v1/abort/${request_id}`, formData)
    await updateBuildQueue()
  } catch (error) {
    emit('toastEvent', AxiosErrorToString(error as AxiosError<string>))
  }
}

async function showBuildLog(build_id: number) {
  const url = `${useAxios().getBaseUrl()}/api/v1/result/${build_id}/build.log`
  window.open(url, '_blank')?.focus()
}

async function getPublicUrl(build_id: number) {
  try {
    const response = await useAxios().get(`/api/v1/public_url/${build_id}/build.log`)
    navigator.clipboard.writeText(response.data.url)
    emit('toastEvent', ['Public URL is copied to clipboard', `It's valid  for ${response.data.ttl} seconds`])
  } catch (error) {
    emit('toastEvent', AxiosErrorToString(error as AxiosError<string>))
  }
}

function isRequested(state: string): boolean {
  return state === "REQUESTED"
}

function isBuilding(state: string): boolean {
  return state === "BUILDING"
}

function isSucceeded(state: string): boolean {
  return state === "SUCCEEDED"
}

function isFailed(state: string): boolean {
  return state === "FAILED"
}

function isAborted(state: string): boolean {
  return state === "ABORTED"
}

function isAbortable(state: string): boolean {
  return isRequested(state) || isBuilding(state)
}

function hasResult(state: string): boolean {
  return isSucceeded(state) || isFailed(state)
}

function stateColor(state: string): string {
  if (isRequested(state))
    return "Bisque"
  else if (isBuilding(state))
    return "Aquamarine"
  else if (isSucceeded(state))
    return "SpringGreen"
  else if (isAborted(state))
    return "Orange"
  return "OrangeRed"
}

function onToggleExpand(i: number) {
  rows.value[i + 1].expanded = rows.value[i].expanded = !rows.value[i].expanded
}

function expandAll(expand: boolean) {
  rows.value.forEach((r) => { r.expanded = expand })
}

const allExpanded: ComputedRef<boolean> = computed(() => {
  return rows.value.every((r) => { return r.expanded })
})
</script>

<template>
  <Paginator :loading="loading" :sync-error="syncError" :total-rows="totalRecords" v-model:page="page"
    v-model:rows-per-page="recordsPerPage" @reload="async () => { await updateBuildQueue() }"
    :storage-prefix="String('queueView')" />

  <div style="margin-top: 1rem;"></div>

  <div class="content">
    <table class="fixed_thead">
      <thead>
        <tr>
          <th style="width: 0rem;">
            <div class="center">
              <span v-if="!allExpanded" @click="expandAll(true)" class="material-icons no-select">unfold_more</span>
              <span v-if="allExpanded" @click="expandAll(false)" class="material-icons no-select">unfold_less</span>
            </div>
          </th>
          <th style="width: 10%; min-width:8rem;">ID</th>
          <th style="width: 10%; min-width:8rem;">State</th>
          <th>Branch</th>
          <th style="width:0rem;"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(r, index) in rows" :key="index" :style="{ 'background-color': r.bgColor }">
          <td v-if="!r.isDetail">
            <div class="center">
              <span v-if="!r.expanded" @click="onToggleExpand(index)"
                class="material-icons no-select">expand_more</span>
              <span v-if="r.expanded" @click="onToggleExpand(index)" class="material-icons no-select">expand_less</span>
            </div>
          </td>
          <td v-if="!r.isDetail">{{ r.request.id }}</td>
          <td v-if="!r.isDetail">
            <mark :style="{ 'background-color': stateColor(r.request.state) }">{{ r.request.state }}</mark>
          </td>
          <td v-if="!r.isDetail">{{ r.request.source_branch }}</td>
          <td v-if="!r.isDetail">
            <div class="center">
              <button @click="abort(r.request.id)" title="Abort" :disabled="!isAbortable(r.request.state)"
                class="small-button">
                <span class="material-icons button-icon">cancel</span>
              </button>
            </div>
          </td>
          <td v-if="r.isDetail && r.expanded" colspan="5">
            <div class="details-box">
              <div v-for="(b, index) in r.builds" :key="index" class="notice build-details">
                {{ b.build_config }}<br>
                <mark :style="{ 'background-color': stateColor(b.state) }">{{ b.state }}</mark><br>
                Build {{ b.id }} / Worker {{ b.worker_id ? b.worker_id : '-' }}<br>
                <div class="center">
                  <button @click="router.push({ path: '/log', query: { serverId: b.worker_id } })" title="Worker log"
                    :disabled="isRequested(b.state)" class="small-button">
                    <span class="material-icons button-icon">article</span>
                  </button>
                  <button @click="showBuildLog(b.id)" title="Build log" :disabled="isRequested(b.state)"
                    class="small-button">
                    <span class="material-icons button-icon">feed</span>
                  </button>
                  <button @click="getPublicUrl(b.id)" title="Copy public URL" :disabled="!hasResult(b.state)"
                    class="small-button">
                    <span class="material-icons button-icon">token</span>
                  </button>
                </div>
              </div>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <div style="margin-top: 1rem;"></div>
</template>

<style scoped>
td:last-child {
  white-space: nowrap;
}

mark {
  font-size: 1rem;
}

.small-button {
  margin: 0.2rem;
  padding: 0 0.04rem;
  font-size: 0;
}

.button-icon {
  font-size: 1.2rem;
}

.center {
  display: flex;
  justify-content: center;
  align-items: center;
}

.details-box {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  white-space: wrap;
}

.build-details {
  margin: 0.5rem;
  padding: 0.5rem;
  min-width: 19rem;
  text-align: center;
}

.no-select {
  cursor: default;
  user-select: none;
}
</style>
