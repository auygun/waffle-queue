<script setup lang="ts">
import { ref } from 'vue';

const syncOn = ref(true)

const setSyncOn = (on: boolean) => {
  syncOn.value = on
}

defineExpose({
  setSyncOn
})
</script>

<template>
  <li>
    <span class="material-icons" v-show="syncOn" title="Server is online" style="cursor:default;color: darkgreen;">check_circle</span>
  </li>
  <li>
    <span class="material-icons" v-show="!syncOn" title="Failed to connect to the server" style="cursor:default;color: darkred;">sync_problem</span>
  </li>
</template>
