<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { useTemplateRef } from 'vue'
import Sync from '@/components/Sync.vue'

const sync = useTemplateRef('sync')
const setSyncOn = (on: boolean) => sync.value?.setSyncOn(on)

function onSyncOnEvent(syncOn: boolean) {
  setSyncOn(syncOn)
}
</script>

<template>
  <header>
    <h1><span class="material-icons">factory</span>WaffleQueue</h1>
    <nav>
      <ul>
        <li>
          <RouterLink to="/home">Home</RouterLink>
        </li>
        <li>
          <RouterLink to="/about">About</RouterLink>
        </li>
        <Sync ref="sync" />
      </ul>
    </nav>
  </header>

  <main>
    <RouterView @sync-on-event="onSyncOnEvent"/>
  </main>

  <footer>
    <p>WaffleQueue was developed by Attila Uygun and is licensed under the MIT license.<br>
      <a href="https://github.com/auygun/waffle-queue">Source code</a>
    </p>
  </footer>
</template>

<style scoped>
h1>span {
  font-size: 60%;
}
</style>
