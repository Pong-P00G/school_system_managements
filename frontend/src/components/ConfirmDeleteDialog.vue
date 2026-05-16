<template>
  <div v-if="show" class="admin-modal-overlay" @click.self="$emit('cancel')">
    <div class="admin-modal admin-modal-sm">
      <div class="flex items-center gap-3 mb-4">
        <div class="shrink-0 w-9 h-9 rounded-full bg-red-50 text-red-600 flex items-center justify-center">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
        <h2 class="!mb-0 text-[1.1rem]">{{ title || 'Confirm Delete' }}</h2>
      </div>

      <p class="text-ink-muted text-[0.9rem] mb-2 leading-relaxed">
        Are you sure you want to delete <strong>{{ itemName }}</strong>?
      </p>

      <p v-if="warning" class="p-3 bg-red-50 border border-red-200 rounded-lg mb-4 text-[0.85rem] text-red-900 leading-snug">
        {{ warning }}
      </p>

      <div class="flex justify-end gap-2 pt-2 border-t border-border-light">
        <button class="admin-btn-cancel" @click="$emit('cancel')" :disabled="deleting">Cancel</button>
        <button
          class="py-2 px-4 bg-red-600 text-white border-0 rounded-md text-[0.85rem] font-medium cursor-pointer transition-colors duration-150 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          @click="$emit('confirm')"
          :disabled="deleting"
        >
          {{ deleting ? 'Deleting...' : 'Delete' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  show: { type: Boolean, default: false },
  title: { type: String, default: 'Confirm Delete' },
  itemName: { type: String, default: '' },
  deleting: { type: Boolean, default: false },
  warning: { type: String, default: 'This action cannot be undone. All associated data will also be permanently deleted.' },
})

const emit = defineEmits(['confirm', 'cancel'])
</script>


