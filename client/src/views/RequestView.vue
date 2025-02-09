<script setup lang="ts">
import { useAxios } from '@/client/axios'
import { ref, type Ref } from 'vue'
import TextInput from '@/components/TextInput.vue'

const emit = defineEmits<{
  toastEvent: [message: string]
}>()

const requestType: Ref<string> = ref("Integration")
const remoteUrl: Ref<string> = ref("")
const sourceBranch: Ref<string> = ref("")
const targetBranch: Ref<string> = ref("")
const buildScript: Ref<string> = ref("")

async function request() {
  try {
    const formData = new FormData()
    formData.append('request-type', requestType.value)
    formData.append('remote-url', remoteUrl.value)
    formData.append('source-branch', sourceBranch.value)
    if (requestType.value === "Integration")
      formData.append('target-branch', targetBranch.value)
    formData.append('build-script', buildScript.value)
    await useAxios().postFormData('/api/v1/request', formData)
  } catch (error) {
    emit('toastEvent', error)
  }
}
</script>

<template>
  <div class="center">
    <label><input type="radio" v-model="requestType" value="Integration"> Integration</label>
    <label><input type="radio" v-model="requestType" value="Build"> Build</label>
  </div>
  <TextInput :icon="'alternate_email'" :placeholder="'Remote URL'" v-model:text="remoteUrl" />
  <div class="fit-stretch">
    <TextInput :icon="'merge_type'" :placeholder="'Source branch'" v-model:text="sourceBranch" />
    <TextInput :icon="'merge_type'" :placeholder="'Target branch'" v-model:text="targetBranch"
      :disabled="requestType === 'Build'" />
  </div>
  <TextInput :icon="'directions_run'" :placeholder="'Build script'" v-model:text="buildScript" />
  <div class="center">
    <button @click="request">Request</button>
  </div>
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
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  column-gap: 1em;
}
</style>
