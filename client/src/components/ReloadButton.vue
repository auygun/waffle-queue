<script setup lang="ts">
const props = defineProps({
  loading: {
    type: Boolean,
    required: true,
  },
})

const emit = defineEmits<{
  reload: []
}>()

function onReload() {
  if (!props.loading) emit('reload')
}
</script>

<template>
  <button class="reload-button" @click="onReload">
    <span v-if="!loading" class="material-icons">refresh</span>
    <span v-if="loading" class="loader"></span>
  </button>
</template>

<style scoped>
.reload-button {
  margin: 0.2rem;
  min-width: 2.6rem;
  height: 2.6rem;
}

.loader {
  margin: 0.2rem;
  width: 1.1rem;
  height: 1.1rem;
  border-radius: 50%;
  display: inline-block;
  border-top: 3px solid var(--accent-text);
  border-right: 3px solid transparent;
  box-sizing: border-box;
  animation: rotation 0.5s linear infinite;
}

@keyframes rotation {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}
</style>
