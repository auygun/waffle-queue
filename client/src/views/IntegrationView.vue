<script setup lang="ts">
import { useAxios } from '@/client/axios'
import { ref, type Ref, useTemplateRef } from 'vue'
import Modal from '@/components/Modal.vue'

const sourceBranchName: Ref<string> = ref("")

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
</script>

<template>
  <div>
    <input v-model="sourceBranchName" placeholder="Source branch" />&nbsp
    <button @click="integrate">Request</button>&nbsp
  </div>

  <Modal ref="modal" />
</template>

<style scoped>
div {
  text-align: center;
}
</style>
