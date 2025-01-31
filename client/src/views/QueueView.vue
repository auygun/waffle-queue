<script setup lang="ts">
import { useAxios } from '@/client/axios'
import { ref, type Ref, useTemplateRef, onMounted, onUnmounted, watch } from 'vue'
import Modal from '@/components/Modal.vue'
import Paginator from '@/components/Paginator.vue'

const emit = defineEmits<{
  syncOnEvent: [syncOn: boolean]
}>()

// Integration arguments
const sourceBranchName: Ref<string> = ref("")

const builds = ref([])

const totalRecords: Ref<number> = ref(120)
const firstRecord: Ref<number> = ref(0)
const recordsPerPage: Ref<number> = ref(5)
watch(firstRecord, (fr) => {
  console.log(fr, firstRecord)
})

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
    emit('syncOnEvent', true)
  } catch (error) {
    emit('syncOnEvent', false)
  }
}

async function abort(build_id: number) {
  try {
    const formData = new FormData()
    await useAxios().postFormData(`/api/v1/abort/${build_id}`, formData)
  } catch (error) {
    showModal(error)
  }
}

let intervalId: number

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
  <div>
    <h3>Integration</h3>
    <input v-model="sourceBranchName" placeholder="Source branch" />&nbsp
    <button @click="integrate">Request</button>&nbsp
    <button @click="clear">Clear</button>
  </div>

  <Paginator :loading="false" :total-rows="totalRecords" v-model:offset="firstRecord"
    v-model:rows-per-page="recordsPerPage" />

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
          <td>{{ build.branch }}</td>
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
