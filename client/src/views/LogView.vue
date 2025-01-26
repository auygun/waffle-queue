<script setup lang="ts">
import { useAxios } from '@/client/axios'
import { ref, useTemplateRef, onMounted, onUnmounted } from 'vue'
import Modal from '@/components/Modal.vue'

const emit = defineEmits<{
  syncOnEvent: [syncOn: boolean]
}>()

const log = ref([])

const modal = useTemplateRef('modal')
const showModal = (msg: string) => modal.value?.showModal(msg)

async function getLog() {
  try {
    const response = await useAxios().get('/api/v1/log')
    log.value = response.data.content
    emit('syncOnEvent', true)
  } catch (error) {
    emit('syncOnEvent', false)
  }
}

let intervalId

onMounted(async () => {
  await getLog()

  intervalId = setInterval(async () => {
    await getLog()
  }, 1000)
})

onUnmounted(() => {
  clearInterval(intervalId)
})
</script>

<template>
  <pre><code v-for="(entry, index) in log" :key="index" v-bind:title="entry.timestamp">{{ entry.severity }}&#9;{{ entry.message }}<br></code></pre>

  <Modal ref="modal" />
</template>
