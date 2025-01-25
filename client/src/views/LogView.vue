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
  <div id="container">
    <div id="log">
      <div id="severity">
        <div v-for="(entry, index) in log" :key="index" v-bind:title="entry.timestamp">
          {{ entry.severity }}
        </div>
      </div>
      <div id="message">
        <div v-for="(entry, index) in log" :key="index">
          {{ entry.message }}
        </div>
      </div>
    </div>
  </div>

  <Modal ref="modal" />
</template>

<style scoped>
#container {
  height: 65vh;
  width: 100%;
}

#log {
  overflow: auto;
  height: 100%;
  white-space: nowrap
}

#severity {
  float: left;
  height: 100%;
  width: 10%;
}

#message {
  float: left;
  height: 100%;
  width: 90%;
}
</style>
