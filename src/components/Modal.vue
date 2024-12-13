<script setup lang="ts">
import { ref } from 'vue';

const dialog = ref<HTMLDialogElement>();
const message = ref("")

const showModal = (msg: string) => {
  message.value = msg;
  dialog.value?.showModal();
}

defineExpose({
  showModal
})
</script>

<template>
  <dialog ref="dialog">
    <form method="dialog">
      <p>{{ message }}</p>
      <button autofocus @click="dialog?.close()">Close</button>
    </form>
  </dialog>
</template>
