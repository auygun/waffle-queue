<script setup lang="ts">
import { useAxios } from '@/client/axios'
import { ref, useTemplateRef, onMounted, onUnmounted } from 'vue'
import Modal from '@/components/Modal.vue'

const emit = defineEmits<{
  syncOnEvent: [syncOn: boolean]
}>()

// Integration arguments
const sourceBranchName = ref("")

const builds = ref([])

const modal = useTemplateRef('modal')
const showModal = (msg: string) => modal.value?.showModal(msg)

async function integrate() {
  try {
    const formData = new FormData()
    formData.append('branch', sourceBranchName.value)
    await useAxios().postFormData('/api/v1/integrate', formData)
  } catch (error) {
    showModal(error)
  }
}

async function clear() {
  try {
    const formData = new FormData()
    await useAxios().postFormData('/api/v1/dev/clear', formData)
  } catch (error) {
    showModal(error)
  }
}

async function getBuilds() {
  try {
    const response = await useAxios().get('/api/v1/builds')
    builds.value = response.data.builds
    console.log("call emit('syncOnEvent', false)")
    emit('syncOnEvent', true)
  } catch (error) {
    emit('syncOnEvent', false)
  }
}

let intervalId

onMounted(async () => {
  await getBuilds()

  intervalId = setInterval(async () => {
    await getBuilds()
  }, 1000)
})

onUnmounted(() => {
  clearInterval(intervalId)
})
</script>

<template>
  <h3>Integration</h3>
  <input v-model="sourceBranchName" placeholder="Source branch" />&nbsp
  <button @click="integrate">Request</button>&nbsp
  <button @click="clear">Clear</button>

  <table width="100%">
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
        <td>{{ build.branch }}</td>
        <td>{{ build.state }}</td>
        <td>
          <div>
            <button>Update</button>&nbsp<button>Delete</button>
          </div>
        </td>
      </tr>
    </tbody>
  </table>

  <Modal ref="modal" />
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
