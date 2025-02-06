<script setup lang="ts">
import { useAxios } from '@/client/axios'
import { ref, type Ref, useTemplateRef } from 'vue'
import Modal from '@/components/Modal.vue'
import TextInput from '@/components/TextInput.vue'

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
  <TextInput :icon="'alternate_email'" :placeholder="'Remote URL'" v-model:text="remoteUrl" />
  <div class="fit-stretch">
    <TextInput :icon="'merge_type'" :placeholder="'Source branch'" v-model:text="sourceBranch" />
    <TextInput :icon="'merge_type'" :placeholder="'Target branch'" v-model:text="targetBranch" />
  </div>
  <TextInput :icon="'directions_run'" :placeholder="'Build script'" v-model:text="buildScript" />
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
  flex: 1 1 auto;
}

.center {
  text-align: center;
}
</style>
