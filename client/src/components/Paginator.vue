<script setup lang="ts">
import { computed, type ComputedRef } from 'vue'

const props = defineProps({
  maxVisibleButtons: {
    type: Number,
    required: false,
    default: 5,
  },
  totalPages: {
    type: Number,
    required: true,
  },
  currentPage: {
    type: Number,
    required: true,
  },
})

const emit = defineEmits<{
  pageChanged: [syncOn: number]
}>()

const startPage: ComputedRef<number> = computed(() => {
  // When on the first page
  if (props.currentPage === 1) {
    return 1
  }

  // When on the last page
  if (props.currentPage === props.totalPages) {
    return props.totalPages - props.maxVisibleButtons
  }

  // When inbetween
  return props.currentPage - 1
})

const pages: ComputedRef<{ name: number, isDisabled: boolean }[]> = computed(() => {
  const range = []

  for (let i = startPage.value;
    i <= Math.min(startPage.value + props.maxVisibleButtons - 1, props.totalPages);
    i++) {
    range.push({
      name: i,
      isDisabled: i === props.currentPage
    })
  }

  return range
})

const isInFirstPage: ComputedRef<boolean> = computed(() => {
  return props.currentPage === 1;
})

const isInLastPage: ComputedRef<boolean> = computed(() => {
  return props.currentPage === props.totalPages;
})

function isPageActive(page: number) {
  return props.currentPage === page;
}

function onClickFirstPage() {
  emit('pageChanged', 1)
}

function onClickPreviousPage() {
  emit('pageChanged', props.currentPage - 1)
}

function onClickPage(page: number) {
  emit('pageChanged', page)
}

function onClickNextPage() {
  emit('pageChanged', props.currentPage + 1)
}

function onClickLastPage() {
  emit('pageChanged', props.totalPages)
}
</script>

<template>
  <div class="paginator">
    <button @click="onClickFirstPage" :disabled="isInFirstPage">
      <span class="material-icons">first_page</span>
    </button>

    <button @click="onClickPreviousPage" :disabled="isInFirstPage">
      <span class="material-icons">navigate_before</span>
    </button>

    <button v-for="page in pages" :key="page.name" :disabled="page.isDisabled"
      :class="{ activepage: isPageActive(page.name) }" @click="onClickPage(page.name)">
      {{ page.name }}
    </button>

    <button @click="onClickNextPage" :disabled="isInLastPage">
      <span class="material-icons">navigate_next</span>
    </button>

    <button @click="onClickLastPage" :disabled="isInLastPage">
      <span class="material-icons">last_page</span>
    </button>
  </div>
</template>

<style scoped>
.paginator {
  text-align: center;
  white-space: nowrap;
}

.paginator>button {
  margin: 0.2rem;
  text-align: center;
  width: 2.6rem;
  height: 2.6rem;
  background-color: transparent;
  border: 1px solid;
  border-color: transparent;
  color: rgba(255, 255, 255, 0.6);
}

.paginator>button:enabled:hover {
  border-color: var(--hover);
  color: var(--accent);
}

.activepage[disabled] {
  border-color: var(--accent);
  color: var(--accent);
  cursor: default;
}

.paginator>button>span {
  vertical-align: middle;
}
</style>
