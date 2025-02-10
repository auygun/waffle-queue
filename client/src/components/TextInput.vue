<script setup lang="ts">
const props = defineProps({
  icon: {
    type: String,
    required: true,
  },
  placeholder: {
    type: String,
    required: false,
    default: "",
  },
  disabled: {
    type: Boolean,
    required: false,
    default: false,
  },
  mirrorIcon: {
    type: Boolean,
    required: false,
    default: false,
  }
})

const textModel = defineModel('text', {
  type: String,
  required: true,
})
</script>

<template>
  <div class="wrapper">
    <div>
      <span class="material-icons" :class="{ mirror: props.mirrorIcon }">{{ props.icon }}</span>
    </div>
    <input v-model.trim="textModel" :disabled="props.disabled" :placeholder="props.placeholder" type="text" />
  </div>
</template>

<style scoped>
.wrapper {
  display: flex;
}

.wrapper>input[type="text"] {
  flex: 1 1 auto;
  border-left: 0;
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
}

.wrapper div {
  display: flex;
  justify-content: center;
  align-items: center;
  padding-left: 0.4rem;
  padding-right: 0.4rem;
  margin-bottom: 0.5rem;
  color: var(--text);
  background-color: var(--border);
  border: 1px solid var(--border);
  border-radius: var(--standard-border-radius);
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.mirror {
  transform: scale(-1, -1);
}
</style>
