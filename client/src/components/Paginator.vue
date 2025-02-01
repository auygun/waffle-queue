<script setup lang="ts">
import { computed, type ComputedRef, watch } from 'vue'
import ReloadButton from '@/components/ReloadButton.vue'

const props = defineProps({
  maxVisibleButtons: {
    type: Number,
    required: false,
    default: 6,
  },
  totalRows: {
    type: Number,
    required: true,
  },
  loading: {
    type: Boolean,
    required: true,
  },
})

const offsetModel = defineModel('offset', {
  type: Number,
  required: true,
})

const rowsPerPageModel = defineModel('rowsPerPage', {
  type: Number,
  required: true,
})

const emit = defineEmits<{
  reload: []
}>()

watch(
  () => props.totalRows,
  (newValue) => {
    if (offsetModel.value >= newValue)
      offsetModel.value = newValue === 0 ? 0 : newValue - 1
  },
  { deep: true }
)

const totalPages: ComputedRef<number> = computed(() => {
  return Math.ceil(props.totalRows / rowsPerPageModel.value)
})

const numVisibleButtons: ComputedRef<number> = computed(() => {
  if (totalPages.value < props.maxVisibleButtons)
    return totalPages.value
  return props.maxVisibleButtons
})

const startPage: ComputedRef<number> = computed((previous) => {
  const value: number = currentPage.value - Math.floor(numVisibleButtons.value / 2)
  if (value < 1)
    return 1
  if (value + numVisibleButtons.value > totalPages.value)
    return totalPages.value - numVisibleButtons.value + 1
  if (previous && numVisibleButtons.value % 2 == 0 &&
    previous > value && currentPage.value - value == numVisibleButtons.value / 2) {
    return value + 1
  }
  return value
})

const currentPage: ComputedRef<number> = computed(() => {
  const page: number = Math.floor(offsetModel.value / rowsPerPageModel.value) + 1
  return page
})

const pages: ComputedRef<{ name: number, isDisabled: boolean }[]> = computed(() => {
  const range = []

  for (let i = startPage.value;
    i <= Math.min(startPage.value + numVisibleButtons.value - 1, totalPages.value);
    i++) {
    range.push({
      name: i,
      isDisabled: i === currentPage.value
    })
  }
  return range
})

const isInFirstPage: ComputedRef<boolean> = computed(() => {
  return totalPages.value === 0 || currentPage.value === 1
})

const isInLastPage: ComputedRef<boolean> = computed(() => {
  return totalPages.value === 0 ? true : currentPage.value === totalPages.value
})

function isPageActive(page: number) {
  return currentPage.value === page
}

function onClickPage(page: number) {
  offsetModel.value = (page - 1) * rowsPerPageModel.value
}
</script>

<template>
  <div class="paginator">
    <ReloadButton :loading="loading" @reload="emit('reload')" />

    <button class="paginator-button" @click="onClickPage(1)" :disabled="isInFirstPage">
      <span class="material-icons">first_page</span>
    </button>

    <button class="paginator-button" @click="onClickPage(currentPage - 1)" :disabled="isInFirstPage">
      <span class="material-icons">navigate_before</span>
    </button>

    <button class="paginator-button" v-for="page in pages" :key="page.name" :disabled="page.isDisabled"
      :class="{ 'active-page': isPageActive(page.name) }" @click="onClickPage(page.name)">
      {{ page.name }}
    </button>

    <button class="paginator-button" @click="onClickPage(currentPage + 1)" :disabled="isInLastPage">
      <span class="material-icons">navigate_next</span>
    </button>

    <button class="paginator-button" @click="onClickPage(totalPages)" :disabled="isInLastPage">
      <span class="material-icons">last_page</span>
    </button>

    <button class="paginator-button">
      <span class="material-icons">remove_circle_outline</span>
    </button>
    <button class="paginator-button">
      <span class="material-icons">add_circle_outline</span>
    </button>
  </div>
</template>

<style scoped>
.paginator {
  display: flex;
  flex-wrap: wrap;
  /* for horizontal aligning of child elements */
  justify-content: center;
  /* for vertical aligning */
  align-items: center;
}

button.paginator-button {
  margin: 0.2rem;
  text-align: center;
  min-width: 2.6rem;
  height: 2.6rem;
  background-color: transparent;
  border: 1px solid;
  border-color: transparent;
  color: var(--text);
  transition: none;
}

button:enabled:hover.paginator-button {
  border-color: var(--border);
  color: var(--text);
}

.active-page[disabled] {
  border-color: var(--accent);
  color: var(--accent);
  cursor: default;
}
</style>
