<script setup lang="ts">
import { useAxios } from '@/main'
import { ref, watchEffect } from 'vue'

const branches = ['main', 'minor']

const currentBranch = ref(branches[0])
const commits = ref([])

watchEffect(async () => {
  const response = await useAxios().get(`/repos/vuejs/core/commits?per_page=3&sha=${currentBranch.value}`)
  commits.value = response.data
})

function truncate(v) {
  const newline = v.indexOf('\n')
  return newline > 0 ? v.slice(0, newline) : v
}

function formatDate(v) {
  return v.replace(/T|Z/g, ' ')
}
</script>

<template>
  <h1>Latest Vue Core Commits</h1>
  <template v-for="branch in branches">
    <input type="radio" :id="branch" :value="branch" name="branch" v-model="currentBranch">
    <label :for="branch">{{ branch }}</label>
  </template>
  <p>vuejs/core@{{ currentBranch }}</p>
  <ul v-if="commits.length > 0">
    <li v-for="{ html_url, sha, author, commit } in commits" :key="sha">
      <a :href="html_url" target="_blank">{{ sha.slice(0, 7) }}</a>
      - <span>{{ truncate(commit.message) }}</span><br>
      by <span>
        <a :href="author.html_url" target="_blank">{{ commit.author.name }}</a>
      </span>
      at <span>{{ formatDate(commit.author.date) }}</span>
    </li>
  </ul>
</template>
