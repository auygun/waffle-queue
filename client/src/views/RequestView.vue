<script setup lang="ts">
import { useAxios } from '@/client/axios'
import { ref, type Ref, watch } from 'vue'
import TextInput from '@/components/TextInput.vue'

const LAST_REQUEST_VIEW_REQUEST_TYPE = "LastRequestViewRequestType"
const LAST_REQUEST_VIEW_REMOTE_URL = "LastRequestViewRemoteUrl"
const LAST_REQUEST_VIEW_SOURCE_BRANCH = "LastRequestViewSourceBranch"
const LAST_REQUEST_VIEW_TARGET_BRANCH = "LastRequestViewTargetBranch"
const LAST_REQUEST_VIEW_BUILD_SCRIPT = "LastRequestViewBuildScript"
const LAST_REQUEST_VIEW_WORK_DIR = "LastRequestViewWorkDir"

const emit = defineEmits<{
  toastEvent: [message: string]
}>()

const requestType: Ref<string> = ref(getRequestType())
const remoteUrl: Ref<string> = ref(getRemoteUrl())
const sourceBranch: Ref<string> = ref(getSourceBranch())
const targetBranch: Ref<string> = ref(getTargetBranch())
const buildScript: Ref<string> = ref(getBuildScript())
const workDir: Ref<string> = ref(getWorkDir())

watch(requestType, (newValue) => {
  localStorage.setItem(LAST_REQUEST_VIEW_REQUEST_TYPE, newValue)
})

watch(remoteUrl, (newValue) => {
  localStorage.setItem(LAST_REQUEST_VIEW_REMOTE_URL, newValue)
})

watch(sourceBranch, (newValue) => {
  localStorage.setItem(LAST_REQUEST_VIEW_SOURCE_BRANCH, newValue)
})

watch(targetBranch, (newValue) => {
  localStorage.setItem(LAST_REQUEST_VIEW_TARGET_BRANCH, newValue)
})

watch(buildScript, (newValue) => {
  localStorage.setItem(LAST_REQUEST_VIEW_BUILD_SCRIPT, newValue)
})

watch(workDir, (newValue) => {
  localStorage.setItem(LAST_REQUEST_VIEW_WORK_DIR, newValue)
})

function getRequestType(): string {
  try {
    const cachedValue = localStorage.getItem(LAST_REQUEST_VIEW_REQUEST_TYPE)
    return cachedValue ? cachedValue : "Integration"
  } catch { return "" }
}

function getRemoteUrl(): string {
  try {
    const cachedValue = localStorage.getItem(LAST_REQUEST_VIEW_REMOTE_URL)
    return cachedValue ? cachedValue : ""
  } catch { return "" }
}

function getSourceBranch(): string {
  try {
    const cachedValue = localStorage.getItem(LAST_REQUEST_VIEW_SOURCE_BRANCH)
    return cachedValue ? cachedValue : ""
  } catch { return "" }
}

function getTargetBranch(): string {
  try {
    const cachedValue = localStorage.getItem(LAST_REQUEST_VIEW_TARGET_BRANCH)
    return cachedValue ? cachedValue : ""
  } catch { return "" }
}

function getBuildScript(): string {
  try {
    const cachedValue = localStorage.getItem(LAST_REQUEST_VIEW_BUILD_SCRIPT)
    return cachedValue ? cachedValue : ""
  } catch { return "" }
}

function getWorkDir(): string {
  try {
    const cachedValue = localStorage.getItem(LAST_REQUEST_VIEW_WORK_DIR)
    return cachedValue ? cachedValue : ""
  } catch { return "" }
}

async function request() {
  try {
    const formData = new FormData()
    formData.append('request-type', requestType.value)
    formData.append('remote-url', remoteUrl.value)
    formData.append('source-branch', sourceBranch.value)
    if (requestType.value === "Integration")
      formData.append('target-branch', targetBranch.value)
    formData.append('build-script', buildScript.value)
    formData.append('work-dir', workDir.value)
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
    <TextInput :icon="'merge_type'" :placeholder="'Target branch'" v-model:text="targetBranch" :mirror-icon="true"
      :disabled="requestType === 'Build'" />
  </div>
  <div class="fit-stretch">
    <TextInput :icon="'directions_run'" :placeholder="'Build script'" v-model:text="buildScript" />
    <TextInput :icon="'directions'" :placeholder="'Work directory'" v-model:text="workDir" />
  </div>
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
