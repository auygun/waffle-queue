<script setup lang="ts">
import { computed, type ComputedRef, onMounted } from 'vue'

const props = defineProps({
  maxVisibleButtons: {
    type: Number,
    required: false,
    default: 5,
  },
  totalRows: {
    type: Number,
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

// const emit = defineEmits<{
//   reload: []
// }>()

const totalPages: ComputedRef<number> = computed(() => {
  return Math.ceil(props.totalRows / rowsPerPageModel.value)
})

const startPage: ComputedRef<number> = computed(() => {
  const value: number = currentPage.value - Math.floor(props.maxVisibleButtons / 2)
  if (value < 1)
    return 1
  if (value + props.maxVisibleButtons > totalPages.value)
    return totalPages.value - props.maxVisibleButtons + 1
  return value
})

const currentPage: ComputedRef<number> = computed(() => {
  return Math.floor(offsetModel.value / rowsPerPageModel.value) + 1
})

const pages: ComputedRef<{ name: number, isDisabled: boolean }[]> = computed(() => {
  const range = []

  for (let i = startPage.value;
    i <= Math.min(startPage.value + props.maxVisibleButtons - 1, totalPages.value);
    i++) {
    range.push({
      name: i,
      isDisabled: i === currentPage.value
    })
  }
  return range
})

const isInFirstPage: ComputedRef<boolean> = computed(() => {
  return currentPage.value === 1
})

const isInLastPage: ComputedRef<boolean> = computed(() => {
  return currentPage.value === totalPages.value
})

function isPageActive(page: number) {
  return currentPage.value === page
}

function onClickPage(page: number) {
  offsetModel.value = (page - 1) * rowsPerPageModel.value
  console.assert(offsetModel.value >= 0, `${offsetModel.value} (offset) is negative`)
  console.assert(offsetModel.value < props.totalRows, `${offsetModel.value} (offset) is greater than ${props.totalRows} (totalRows)`)
}

onMounted(() => {
  const remainder = offsetModel.value % rowsPerPageModel.value
  console.assert(remainder == 0, `${offsetModel.value} (offset) is not multiple of ${rowsPerPageModel.value} (rowsPerPage)`)
  if (remainder > 0) {
    offsetModel.value -= remainder
  }
})
</script>

<template>
  <div class="paginator">
    <button @click="onClickPage(1)" :disabled="isInFirstPage">
      <span class="material-icons">first_page</span>
    </button>

    <button @click="onClickPage(currentPage - 1)" :disabled="isInFirstPage">
      <span class="material-icons">navigate_before</span>
    </button>

    <button v-for="page in pages" :key="page.name" :disabled="page.isDisabled"
      :class="{ 'active-page': isPageActive(page.name) }" @click="onClickPage(page.name)">
      {{ page.name }}
    </button>

    <button @click="onClickPage(currentPage + 1)" :disabled="isInLastPage">
      <span class="material-icons">navigate_next</span>
    </button>

    <button @click="onClickPage(totalPages)" :disabled="isInLastPage">
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
  min-width: 2.6rem;
  height: 2.6rem;
  background-color: transparent;
  border: 1px solid;
  border-color: transparent;
  color: var(--text-light);
}

.paginator>button:enabled:hover {
  border-color: var(--hover);
  color: var(--text-light);
}

.active-page[disabled] {
  border-color: var(--accent);
  color: var(--accent);
  cursor: default;
}

.paginator>button>span {
  vertical-align: middle;
}
</style>
