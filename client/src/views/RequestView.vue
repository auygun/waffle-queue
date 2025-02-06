<script setup lang="ts">
import { useAxios } from '@/client/axios'
import { ref, type Ref, useTemplateRef } from 'vue'
import Modal from '@/components/Modal.vue'

const remoteUrl: Ref<string> = ref("")
const sourceBranch: Ref<string> = ref("")
const targetBranch: Ref<string> = ref("")
const buildScript: Ref<string> = ref("")

const modal = useTemplateRef('modal')
const showModal = (msg: string) => modal.value?.showModal(msg)

async function integrate() {
  try {
    const formData = new FormData()
    formData.append('branch', sourceBranch.value)
    await useAxios().postFormData('/api/v1/integrate', formData)
  } catch (error) {
    showModal(error)
  }
}
</script>

<template>
  <h3 class="center">Request integration</h3>
  <input v-model="remoteUrl" placeholder="Remote URL" />
  <div class="fit-stretch">
    <input v-model="sourceBranch" placeholder="Source branch" />
    <input v-model="targetBranch" placeholder="Target branch" />
  </div>
  <input v-model="buildScript" placeholder="Build script" />
  <div class="center">
    <button @click="integrate">Request</button>
  </div>

  <Modal ref="modal" />
</template>

<style scoped>
.fit-stretch {
  display: flex;
  flex-wrap: wrap;
  column-gap: 1em;
}

.fit-stretch>* {
  flex: 1;
}

.center {
  text-align: center;
}
</style>
