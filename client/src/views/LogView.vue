<script setup lang="ts">
import { AxiosErrorToString, useAxios } from '@/client/axios'
import { ref, type Ref, onMounted } from 'vue'
import ReloadButton from '@/components/ReloadButton.vue'
import type { AxiosError } from 'axios';

const emit = defineEmits<{
  toastEvent: [message: [string, string]]
}>()

const log = ref([])
const loading: Ref<boolean> = ref(false)
const syncError: Ref<boolean> = ref(false)

async function getLog() {
  loading.value = true
  syncError.value = false
  try {
    const response = await useAxios().get('/api/v1/log')
    log.value = response.data.content
  } catch (error) {
    syncError.value = true
    emit('toastEvent', AxiosErrorToString(error as AxiosError<string>))
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await getLog()
})
</script>

<template>
  <div class="center">
    <ReloadButton :loading="loading" :sync-error="syncError" @reload="async () => { await getLog() }" />
  </div>
  <pre><code v-for="(entry, index) in log" :key="index" v-bind:title="entry.timestamp">{{ entry.severity }}&#9;{{ entry.message }}<br></code></pre>
</template>

<style scoped>
.center {
  text-align: center;
}
</style>
