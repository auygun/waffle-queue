<script setup lang="ts">
import { type AxiosResponse } from 'axios'
import { useAxios } from '@/client/axios'
import { ref, watchEffect, useTemplateRef } from 'vue'
import Modal from '@/components/Modal.vue'

const branches = ['main', 'minor']

const currentBranch = ref(branches[0])
const commits = ref([])

const modal = useTemplateRef('modal')
const showModal = (msg: string) => modal.value.showModal(msg)

async function fetchCommits(
  sha: string,
): Promise<AxiosResponse> {
  return useAxios().get(`/repos/vuejs/core/commits?per_page=3&sha=${currentBranch.value}`)
}

watchEffect(() => {
  fetchCommits(currentBranch.value).then(
    (response) => {
      commits.value = response.data
    },
    (error) => {
      showModal(error);
    },
  )
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

  <table width="100%">
    <thead>
      <tr>
        <th>Title</th>
        <th>Author</th>
        <th>Read?</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Harry Potter and the Philosopher's Stone</td>
        <td>J. K. Rowling</td>
        <td><span>No</span></td>
        <td>
          <div>
            <button>Update</button>&nbsp<button>Delete</button>
          </div>
        </td>
      </tr>
      <tr>
        <td>On the Road</td>
        <td>Jack Kerouac</td>
        <td><span>Yes</span></td>
        <td>
          <div>
            <button>Update</button>&nbsp<button>Delete</button>
          </div>
        </td>
      </tr>
    </tbody>
  </table>

  <ul v-if="commits.length > 0">
    <li v-for="{ html_url, sha, author, commit } in commits" :key="sha">
      <a :href="html_url" target="_blank">{{ sha.slice(0, 7) }}</a>
      - <span>{{ truncate(commit.message) }}</span><br>
      by <span>
        <a :href="author?.html_url" target="_blank">{{ commit.author?.name }}</a>
      </span>
      at <span>{{ formatDate(commit.author?.date) }}</span>
    </li>
  </ul>

  <Modal ref="modal" />
</template>

<style scoped>
td:last-child {
    width: 1%;
    white-space: nowrap;
}

td>div>button {
  padding: 0;
}
</style>
