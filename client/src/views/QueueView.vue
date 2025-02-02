<script setup lang="ts">
import { useAxios } from '@/client/axios'
import { ref, type Ref, useTemplateRef, onMounted, watch } from 'vue'
import Modal from '@/components/Modal.vue'
import Paginator from '@/components/Paginator.vue'

// Integration arguments
const sourceBranchName: Ref<string> = ref("")

const builds = ref([])

const totalRecords: Ref<number> = ref(0)
const page: Ref<number> = ref(1)
const recordsPerPage: Ref<number> = ref(5)
const loading: Ref<boolean> = ref(false)

watch([page, recordsPerPage], async () => {
  await getBuilds()
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
  loading.value = true
  try {
    const response = await useAxios().get('/api/v1/builds', {
      offset: (page.value - 1) * recordsPerPage.value,
      limit: recordsPerPage.value,
    })
    totalRecords.value = response.data.count
    builds.value = response.data.content
  } catch (error) {
  } finally {
    loading.value = false
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

onMounted(async () => {
  await getBuilds()
})
</script>

<template>
  <div>
    <h3>Integration</h3>
    <input v-model="sourceBranchName" placeholder="Source branch" />&nbsp
    <button @click="integrate">Request</button>&nbsp
    <button @click="clear">Clear</button>
  </div>

  <Paginator :loading="loading" :total-rows="totalRecords" v-model:page="page" v-model:rows-per-page="recordsPerPage"
    @reload="async () => { await getBuilds() }" :storage-prefix="String('queueView')" />

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
