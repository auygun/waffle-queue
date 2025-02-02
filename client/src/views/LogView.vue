<script setup lang="ts">
import { useAxios } from '@/client/axios'
import { ref, type Ref, useTemplateRef, onMounted } from 'vue'
import ReloadButton from '@/components/ReloadButton.vue'
import Modal from '@/components/Modal.vue'

const log = ref([])
const loading: Ref<boolean> = ref(false)

const modal = useTemplateRef('modal')
const showModal = (msg: string) => modal.value?.showModal(msg)

async function getLog() {
  loading.value = true
  try {
    const response = await useAxios().get('/api/v1/log')
    log.value = response.data.content
  } catch (error) {
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await getLog()
})
</script>

<template>
  <div class="horizontal-bar">
    <ReloadButton :loading="loading" @reload="async () => { await getLog() }" />
  </div>
  <pre><code v-for="(entry, index) in log" :key="index" v-bind:title="entry.timestamp">{{ entry.severity }}&#9;{{ entry.message }}<br></code></pre>

  <Modal ref="modal" />
</template>
