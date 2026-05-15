<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentPage: { type: Number, required: true },
  totalItems: { type: Number, required: true },
  pageSize: { type: Number, default: 100 },
})

const emit = defineEmits(['page-change'])

const totalPages = computed(() => Math.max(1, Math.ceil(props.totalItems / props.pageSize)))

const startItem = computed(() => (props.currentPage - 1) * props.pageSize + 1)
const endItem = computed(() => Math.min(props.currentPage * props.pageSize, props.totalItems))

const visiblePages = computed(() => {
  const pages = []
  const total = totalPages.value
  const cur = props.currentPage

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    pages.push(1)
    if (cur > 3) pages.push('…')
    const start = Math.max(2, cur - 1)
    const end = Math.min(total - 1, cur + 1)
    for (let i = start; i <= end; i++) pages.push(i)
    if (cur < total - 2) pages.push('…')
    pages.push(total)
  }
  return pages
})

const goTo = (page) => {
  if (page >= 1 && page <= totalPages.value && page !== props.currentPage) {
    emit('page-change', page)
  }
}
</script>

<template>
  <div v-if="totalItems > pageSize" class="flex flex-col sm:flex-row items-center justify-between gap-3 px-6 py-3 border-t border-border-light bg-white rounded-b-xl">
    <span class="text-sm text-ink-muted">
      Showing <span class="font-medium text-ink">{{ startItem }}</span>–<span class="font-medium text-ink">{{ endItem }}</span> of <span class="font-medium text-ink">{{ totalItems }}</span>
    </span>

    <div class="flex items-center gap-1">
      <button
        :disabled="currentPage === 1"
        class="px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors disabled:opacity-30 disabled:cursor-not-allowed hover:bg-gray-100 text-ink-muted"
        @click="goTo(currentPage - 1)"
      >
        ← Prev
      </button>

      <template v-for="(p, i) in visiblePages" :key="i">
        <span v-if="p === '…'" class="px-1.5 text-ink-muted text-xs">…</span>
        <button
          v-else
          class="min-w-[32px] px-2 py-1.5 rounded-md text-xs font-medium transition-colors"
          :class="p === currentPage
            ? 'bg-primary text-white shadow-sm'
            : 'text-ink-muted hover:bg-gray-100 hover:text-ink'"
          @click="goTo(p)"
        >
          {{ p }}
        </button>
      </template>

      <button
        :disabled="currentPage === totalPages"
        class="px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors disabled:opacity-30 disabled:cursor-not-allowed hover:bg-gray-100 text-ink-muted"
        @click="goTo(currentPage + 1)"
      >
        Next →
      </button>
    </div>
  </div>
</template>
