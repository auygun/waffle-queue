<script setup lang="ts">
import { ref, type Ref, useTemplateRef } from 'vue';

const toast = useTemplateRef<HTMLDivElement>('toast');
const message: Ref<[string, string]> = ref(["", ""])

let toastTimeout: number | null = null

const showToast = (msg: [string, string]) => {
  message.value[0] = msg[0];
  message.value[1] = msg[1];
  toast.value.className = "notice show";
  maybeClearUpdateTimeout()
  toastTimeout = setTimeout(hideToast, 3000);
}

function hideToast() {
  toast.value.className = toast.value.className.replace("show", "hide");
  toastTimeout = setTimeout(clearToast, 290);
}

function clearToast() {
  toast.value.className = toast.value.className.replace("hide", "");
}

function maybeClearUpdateTimeout() {
  if (toastTimeout !== null) {
    clearTimeout(toastTimeout)
    toastTimeout = null
  }
}

defineExpose({
  showToast
})
</script>

<template>
  <div class="notice" id="toast" ref="toast">{{ message[0] }}<br>{{ message[1] }}</div>
</template>

<style scoped>
#toast {
  visibility: hidden;
  text-align: center;
  overflow-wrap: break-word;
  min-width: min(100rem, 90vw);
  max-width: min(100rem, 90vw);
  position: fixed;
  z-index: 1;
  bottom: 70px;
}

#toast.show {
  visibility: visible;
  -webkit-animation: fadein 0.3s;
  animation: fadein 0.3s;
}

#toast.hide {
  visibility: visible;
  -webkit-animation: fadeout 0.3s;
  animation: fadeout 0.3s;
}

/* Animations to fade the toast in and out */
@-webkit-keyframes fadein {
  from {
    bottom: 0;
    opacity: 0;
  }

  to {
    bottom: 70px;
    opacity: 1;
  }
}

@keyframes fadein {
  from {
    bottom: 0;
    opacity: 0;
  }

  to {
    bottom: 70px;
    opacity: 1;
  }
}

@-webkit-keyframes fadeout {
  from {
    bottom: 70px;
    opacity: 1;
  }

  to {
    bottom: 0;
    opacity: 0;
  }
}

@keyframes fadeout {
  from {
    bottom: 70px;
    opacity: 1;
  }

  to {
    bottom: 0;
    opacity: 0;
  }
}
</style>
