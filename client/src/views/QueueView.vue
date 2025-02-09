<script setup lang="ts">
import { useAxios } from '@/client/axios'
import { ref, type Ref, watch } from 'vue'
import router from '@/router'
import Paginator from '@/components/Paginator.vue'

const LAST_QUEUE_VIEW_RECORDS_PER_PAGE = "LastQueueViewRecordsPerPage"

const props = defineProps({
  offset: {
    type: String,
    default: '0',
  },
})

const emit = defineEmits<{
  toastEvent: [message: string]
}>()

const builds = ref([])

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
  } catch (error) {
    syncError.value = true
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
    emit('toastEvent', error)
  }
}
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
          <th>ID</th>
          <th>Branch</th>
          <th>State</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(build, index) in builds" :key="index">
          <td>{{ build.id }}</td>
          <td>{{ build.source_branch }}</td>
          <td>{{ build.state }}</td>
          <td>
            <div>
              <button @click="abort(build.id)">Abort</button>
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
  width: 1%;
  font-size: 0.9rem;
  white-space: nowrap;
}

td>div>button {
  padding: 0;
}
</style>
