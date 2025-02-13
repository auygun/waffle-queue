<script setup lang="ts">
import { AxiosErrorToString, useAxios } from '@/client/axios'
import { computed, type ComputedRef, ref, type Ref, watch } from 'vue'
import router from '@/router'
import Paginator from '@/components/Paginator.vue'
import type { AxiosError } from 'axios'

const LAST_QUEUE_VIEW_RECORDS_PER_PAGE = "LastQueueViewRecordsPerPage"

type Build = {
  id: number
  integration: boolean
  remote_url: string
  source_branch: string
  target_branch: string
  build_script: string
  state: string
}

type Row = {
  build: Build
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

const builds: Ref<Build[]> = ref([])

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
    await updateBuilds()
  },
  { immediate: true }
)

watch(recordsPerPage,
  async (newValue) => {
    localStorage.setItem(LAST_QUEUE_VIEW_RECORDS_PER_PAGE, newValue.toString())
    await updateBuilds()
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

async function updateBuilds() {
  loading.value = true
  syncError.value = false
  try {
    const response = await useAxios().get('/api/v1/builds', {
      offset: Number(props.offset),
      limit: recordsPerPage.value,
    })
    totalRecords.value = response.data.count
    builds.value = response.data.content
    rows.value = []
    for (let i = 0; i < builds.value.length; ++i) {
      const color = i % 2 !== 0 ? "var(--accent-bg)" : "var(--bg)"
      rows.value.push({ build: builds.value[i], isDetail: false, expanded: false, bgColor: color })
      rows.value.push({ build: builds.value[i], isDetail: true, expanded: false, bgColor: color })
    }
  } catch (error) {
    syncError.value = true
    emit('toastEvent', AxiosErrorToString(error as AxiosError<string>))
  } finally {
    loading.value = false
  }
}

async function abort(build_id: number) {
  try {
    const formData = new FormData()
    await useAxios().postFormData(`/api/v1/abort/${build_id}`, formData)
    await updateBuilds()
  } catch (error) {
    emit('toastEvent', AxiosErrorToString(error as AxiosError<string>))
  }
}

function isRequested(build: Build): boolean {
  return build.state === "REQUESTED"
}

function isBuilding(build: Build): boolean {
  return build.state === "BUILDING"
}

function isSucceeded(build: Build): boolean {
  return build.state === "SUCCEEDED"
}

function isAborted(build: Build): boolean {
  return build.state === "ABORTED"
}

function isAbortable(build: Build): boolean {
  return isRequested(build) || isBuilding(build)
}

function stateColor(build: Build): string {
  if (isRequested(build))
    return "Bisque"
  else if (isBuilding(build))
    return "Aquamarine"
  else if (isSucceeded(build))
    return "SpringGreen"
  else if (isAborted(build))
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
    v-model:rows-per-page="recordsPerPage" @reload="async () => { await updateBuilds() }"
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
          <td v-if="!r.isDetail">{{ r.build.id }}</td>
          <td v-if="!r.isDetail">
            <mark :style="{ 'background-color': stateColor(r.build) }">{{ r.build.state }}</mark>
          </td>
          <td v-if="!r.isDetail">{{ r.build.source_branch }}</td>
          <td v-if="!r.isDetail">
            <div class="center">
              <button @click="abort(r.build.id)" title="Abort" :disabled="!isAbortable(r.build)">
                <span class="material-icons">cancel</span>
              </button>
            </div>
          </td>
          <td v-if="r.isDetail && r.expanded" colspan="5">
            <div style="white-space: wrap;">
              {{ r.build }}
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <div style="margin-top: 1rem;"></div>
</template>

<style scoped>
td:last-child,
td:nth-child(3) {
  font-size: 0.9rem;
  white-space: nowrap;
}

td>div>button {
  margin: 0.2rem;
  padding: 0 0.04rem;
  font-size: 0;
}

td>div>button>span {
  font-size: 1.0rem;
}

.center {
  display: flex;
  justify-content: center;
  align-items: center;
}

.no-select {
  cursor: default;
  user-select: none;
}
</style>
