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
  syncError: {
    type: Boolean,
    required: true,
  },
  storagePrefix: {
    type: String,
    required: true,
  }
})

const currentPageModel = defineModel('page', {
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

watch(() => props.totalRows,
  () => {
    if (currentPageModel.value > totalPages.value)
      currentPageModel.value = totalPages.value === 0 ? 1 : totalPages.value
  }
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
  const value: number = currentPageModel.value - Math.floor(numVisibleButtons.value / 2)
  if (value < 1)
    return 1
  if (value + numVisibleButtons.value > totalPages.value)
    return totalPages.value - numVisibleButtons.value + 1
  if (previous && numVisibleButtons.value % 2 === 0 &&
    previous > value && currentPageModel.value - value === numVisibleButtons.value / 2) {
    return value + 1
  }
  return value
})

const pages: ComputedRef<{ name: number, isDisabled: boolean }[]> = computed(() => {
  const range = []

  for (let i = startPage.value;
    i <= Math.min(startPage.value + numVisibleButtons.value - 1, totalPages.value);
    i++) {
    range.push({
      name: i,
      isDisabled: i === currentPageModel.value
    })
  }
  return range
})

const isInFirstPage: ComputedRef<boolean> = computed(() => {
  return totalPages.value === 0 || currentPageModel.value === 1
})

const isInLastPage: ComputedRef<boolean> = computed(() => {
  return totalPages.value === 0 ? true : currentPageModel.value === totalPages.value
})

function isPageActive(page: number) {
  return currentPageModel.value === page
}

function onClickPage(page: number) {
  currentPageModel.value = page
}

function onClickRowsPerPage(delta: number) {
  let value: number = rowsPerPageModel.value + delta
  if (value > 30) {
    value = 30
  } else if (value < 5) {
    value = 5
  }
  rowsPerPageModel.value = value;
  const numPages: number = Math.ceil(props.totalRows / value)
  if (numPages > 0 && currentPageModel.value > numPages) {
    currentPageModel.value = numPages
  }
}

</script>

<template>
  <div class="paginator">
    <ReloadButton :loading="loading" :sync-error="syncError" @reload="emit('reload')" />

    <button class="paginator-button" @click="onClickPage(1)" :disabled="isInFirstPage">
      <span class="material-icons">first_page</span>
    </button>

    <button class="paginator-button" @click="onClickPage(currentPageModel - 1)" :disabled="isInFirstPage">
      <span class="material-icons">navigate_before</span>
    </button>

    <button class="paginator-button" v-for="page in pages" :key="page.name" :disabled="page.isDisabled"
      :class="{ 'active-page': isPageActive(page.name) }" @click="onClickPage(page.name)">
      {{ page.name }}
    </button>

    <button class="paginator-button" @click="onClickPage(currentPageModel + 1)" :disabled="isInLastPage">
      <span class="material-icons">navigate_next</span>
    </button>

    <button class="paginator-button" @click="onClickPage(totalPages)" :disabled="isInLastPage">
      <span class="material-icons">last_page</span>
    </button>

    <button class="paginator-button" @click="onClickRowsPerPage(-1)" :disabled="rowsPerPageModel <= 5">
      <span class="material-icons">remove_circle_outline</span>
    </button>
    <button class="paginator-button" @click="onClickRowsPerPage(1)" :disabled="rowsPerPageModel >= 30">
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
  background-color: var(--bg);
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
