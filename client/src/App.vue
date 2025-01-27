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
  <header class="header">
    <h1><span class="material-icons">factory</span>WaffleQueue</h1>
    <nav>
      <ul>
        <li>
          <RouterLink to="/queue">Build Queue</RouterLink>
        </li>
        <li>
          <RouterLink to="/log">Log</RouterLink>
        </li>
        <li>
          <RouterLink to="/about">About</RouterLink>
        </li>
        <div style="padding-left: 1rem;">
          <Sync ref="sync" />
        </div>
      </ul>
    </nav>
  </header>

  <main class="content">
    <div class="inner">
      <div class="content">
        <RouterView @sync-on-event="onSyncOnEvent" />
      </div>
    </div>
  </main>

  <footer class="footer">
    <p>
      <a href="https://github.com/auygun/waffle-queue" target="_blank">WaffleQueue</a>
      was developed by Attila Uygun and is licensed under the MIT license.
    </p>
  </footer>
</template>

<style scoped>
h1>span {
  font-size: 60%;
}
</style>
