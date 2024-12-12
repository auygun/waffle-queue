<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header>
    <h1><span class="material-icons">factory</span>Builder</h1>
    <nav>
      <RouterLink to="/">Home</RouterLink>
      <RouterLink to="/about">About</RouterLink>
    </nav>
  </header>

  <main>
    <RouterView />
  </main>

  <footer>
    <p>Simple.css was created by <a href="https://kevquirk.com">Kev Quirk</a> and is licensed under the MIT license.<br>
      <a href="https://github.com/kevquirk/simple.css-site">Source code for this site</a>
    </p>
  </footer>
</template>

<style scoped>
h1>span {
  font-size: 60%;
}
</style>
