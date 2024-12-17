<script setup lang="ts">
import { type AxiosResponse } from 'axios'
import { useAxios } from '@/client/axios'
import { ref, watchEffect, useTemplateRef, onMounted } from 'vue'
import Modal from '@/components/Modal.vue'

const branches = ['main', 'minor']

const currentBranch = ref(branches[0])
const commits = ref([])
let books = ref([])

const modal = useTemplateRef('modal')
const showModal = (msg: string) => modal.value.showModal(msg)

async function fetchCommits(
  sha: string,
): Promise<AxiosResponse> {
  return useAxios().get(`/repos/vuejs/core/commits?per_page=3&sha=${currentBranch.value}`)
}

async function fetchBooks(): Promise<AxiosResponse> {
  return useAxios().get(`http://localhost:5001/books`)
}

function getBooks() {
  fetchBooks().then(
    (response) => {
      books.value = response.data.books
    },
    (error) => {
      showModal(error);
    },
  )
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

onMounted(() => {
  getBooks();
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
      <tr v-for="(book, index) in books" :key="index">
        <td>{{ book.title }}</td>
        <td>{{ book.author }}</td>
        <td>
          <span v-if="book.read">Yes</span>
          <span v-else>No</span>
        </td>
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
