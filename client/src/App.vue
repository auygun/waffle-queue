<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { useTemplateRef } from 'vue'
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
      </ul>
    </nav>
  </header>

  <main class="content">
    <div class="inner">
      <div class="content">
        <RouterView />
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
