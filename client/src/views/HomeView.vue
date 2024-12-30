<script setup lang="ts">
import { useAxios } from '@/client/axios'
import { ref, watchEffect, useTemplateRef, onMounted, onUnmounted } from 'vue'
import Modal from '@/components/Modal.vue'

const branches = ['main', 'minor']

let builds = ref([])

const modal = useTemplateRef('modal')
const showModal = (msg: string) => modal.value.showModal(msg)

async function integrate(branchName: string) {
  try {
    const formData = new FormData()
    formData.append('branch', branchName)
    await useAxios().postFormData('/api/v1/integrate', formData)
  } catch (error) {
    showModal(error)
  }
}

async function getBuilds() {
  try {
    const response = await useAxios().get('/api/v1/builds')
    builds.value = response.data.builds
  } catch (error) {
    showModal(error)
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
