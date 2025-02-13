<script setup lang="ts">
import { AxiosErrorToString, useAxios } from '@/client/axios'
import { ref, watch, type Ref } from 'vue'
import ReloadButton from '@/components/ReloadButton.vue'
import type { AxiosError } from 'axios';
import router from '@/router';

const LAST_LOG_VIEW_MAX_SEVERITY = "LastLogViewMaxSeverity"

const props = defineProps({
  buildId: {
    type: String,
    default: '',
  },
})

const emit = defineEmits<{
  toastEvent: [message: [string, string]]
}>()

const buildIdInput: Ref<string> = ref("")
const maxSeverity: Ref<string> = ref(getMaxSeverity("TRACE"))
const log = ref([])
const loading: Ref<boolean> = ref(false)
const syncError: Ref<boolean> = ref(false)

watch(buildIdInput,
  () => {
    router.replace({ query: { buildId: buildIdInput.value } })
  }
)

watch(() => props.buildId,
  async () => {
    buildIdInput.value = props.buildId
    await updateLog()
  },
  { immediate: true }
)

watch(maxSeverity,
  async (newValue) => {
    localStorage.setItem(LAST_LOG_VIEW_MAX_SEVERITY, newValue.toString())
    await updateLog()
  }
)

function getMaxSeverity(defaultValue: string): string {
  try {
    const cachedValue = localStorage.getItem(LAST_LOG_VIEW_MAX_SEVERITY)
    return cachedValue ? cachedValue : defaultValue
  } catch { return defaultValue }
}

async function updateLog() {
  if (props.buildId === '')
    return
  loading.value = true
  syncError.value = false
  try {
    const response = await useAxios().get('/api/v1/log', {
      build_id: props.buildId,
      max_severity: maxSeverity.value,
    })
    log.value = response.data.content
  } catch (error) {
    syncError.value = true
    emit('toastEvent', AxiosErrorToString(error as AxiosError<string>))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="center">
    <ReloadButton :loading="loading" :sync-error="syncError" @reload="async () => { await updateLog() }" />
    <input class="align-input" v-model.lazy.trim="buildIdInput" placeholder="Build id" type="text" />
    <select class="align-input" v-model="maxSeverity">
      <option value="FATAL">Fatal</option>
      <option value="ERROR">Error</option>
      <option value="WARN">Warning</option>
      <option value="INFO">Info</option>
      <option value="DEBUG">Debug</option>
      <option value="TRACE">Trace</option>
    </select>
  </div>
  <pre><code v-for="(entry, index) in log" :key="index" v-bind:title="entry.timestamp">{{ entry.severity }}&#9;{{ entry.message }}<br></code></pre>
</template>

<style scoped>
.center {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
}

.align-input {
  margin: 0.2rem;
  width: 7rem;
  height: 2.6rem;
}
</style>
