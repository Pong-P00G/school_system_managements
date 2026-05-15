<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  placeholder: { type: String, default: 'Search...' },
  modelValue: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'search'])

const query = ref(props.modelValue)

// Sync external modelValue changes
watch(() => props.modelValue, (val) => {
  if (val !== query.value) query.value = val
})

// Emit with debounce
let debounceTimer
watch(query, (val) => {
  emit('update:modelValue', val)
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    emit('search', val)
  }, 300)
})

const clearSearch = () => {
  query.value = ''
  emit('update:modelValue', '')
  emit('search', '')
}
</script>

<template>
  <div class="flex items-center gap-2">
    <div class="relative flex-1 max-w-xs">
      <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-muted pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" />
      </svg>
      <input
        v-model="query"
        :placeholder="placeholder"
        class="w-full pl-9 pr-8 py-2 text-sm border border-border-medium rounded-lg bg-surface text-ink placeholder:text-ink-muted focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all"
      />
      <button
        v-if="query"
        class="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded text-ink-muted hover:text-ink hover:bg-gray-100 transition-colors"
        @click="clearSearch"
        title="Clear search"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  </div>
</template>
