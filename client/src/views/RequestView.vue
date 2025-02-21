<script setup lang="ts">
import { AxiosErrorToString, useAxios } from '@/client/axios'
import { ref, type Ref, watch } from 'vue'
import TextInput from '@/components/TextInput.vue'
import type { AxiosError } from 'axios'

const LAST_REQUEST_VIEW_REQUEST_TYPE = "LastRequestViewRequestType"
const LAST_REQUEST_VIEW_PROJECT = "LastRequestViewProject"
const LAST_REQUEST_VIEW_SOURCE_BRANCH = "LastRequestViewSourceBranch"
const LAST_REQUEST_VIEW_TARGET_BRANCH = "LastRequestViewTargetBranch"

const emit = defineEmits<{
  toastEvent: [message: [string, string]]
}>()

const requestType: Ref<string> = ref(getRequestType())
const project: Ref<string> = ref(getProject())
const sourceBranch: Ref<string> = ref(getSourceBranch())
const targetBranch: Ref<string> = ref(getTargetBranch())

watch(requestType, (newValue) => {
  localStorage.setItem(LAST_REQUEST_VIEW_REQUEST_TYPE, newValue)
})

watch(project, (newValue) => {
  localStorage.setItem(LAST_REQUEST_VIEW_PROJECT, newValue)
})

watch(sourceBranch, (newValue) => {
  localStorage.setItem(LAST_REQUEST_VIEW_SOURCE_BRANCH, newValue)
})

watch(targetBranch, (newValue) => {
  localStorage.setItem(LAST_REQUEST_VIEW_TARGET_BRANCH, newValue)
})

function getRequestType(): string {
  try {
    const cachedValue = localStorage.getItem(LAST_REQUEST_VIEW_REQUEST_TYPE)
    return cachedValue ? cachedValue : "Integration"
  } catch { return "" }
}

function getProject(): string {
  try {
    const cachedValue = localStorage.getItem(LAST_REQUEST_VIEW_PROJECT)
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

async function request() {
  try {
    const formData = new FormData()
    formData.append('request-type', requestType.value)
    formData.append('project-name', project.value)
    formData.append('source-branch', sourceBranch.value)
    if (requestType.value === "Integration")
      formData.append('target-branch', targetBranch.value)
    await useAxios().postFormData('/api/v1/new_request', formData)
  } catch (error) {
    emit('toastEvent', AxiosErrorToString(error as AxiosError<string>))
  }
}
</script>

<template>
  <div class="center">
    <label><input type="radio" v-model="requestType" value="Integration"> Integration</label>
    <label><input type="radio" v-model="requestType" value="Build"> Build</label>
  </div>
  <TextInput :icon="'workspaces'" :placeholder="'Project'" v-model:text="project" />
  <div class="fit-stretch">
    <TextInput :icon="'merge_type'" :placeholder="'Source branch'" v-model:text="sourceBranch" />
    <TextInput :icon="'merge_type'" :placeholder="'Target branch'" v-model:text="targetBranch" :mirror-icon="true"
      :disabled="requestType === 'Build'" />
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
