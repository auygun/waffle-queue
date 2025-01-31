<script setup lang="ts">
defineProps({
  loading: {
    type: Boolean,
    required: true,
  },
})

const emit = defineEmits<{
  reload: []
}>()
</script>

<template>
  <button class="reload-button" @click="emit('reload')">
    <span class="material-icons" :class="{ 'spinning-icon': loading }">refresh</span>
  </button>
</template>

<style scoped>
.reload-button {
  margin: 0.2rem;
  min-width: 2.6rem;
  height: 2.6rem;
}

.spinning-icon {
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
