<template>
  <div v-if="show" class="admin-modal-overlay" @click.self="$emit('cancel')">
    <div class="admin-modal admin-modal-sm">
      <div class="delete-dialog-header">
        <div class="delete-dialog-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
        <h2>{{ title || 'Confirm Delete' }}</h2>
      </div>

      <p class="delete-dialog-msg">
        Are you sure you want to delete <strong>{{ itemName }}</strong>?
      </p>

      <p class="delete-dialog-warning" v-if="warning">
        {{ warning }}
      </p>

      <div class="delete-dialog-actions">
        <button class="admin-btn-cancel" @click="$emit('cancel')" :disabled="deleting">Cancel</button>
        <button
          class="admin-btn-delete"
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

<style scoped>
.delete-dialog-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.delete-dialog-header h2 {
  margin-bottom: 0;
  font-size: 1.1rem;
}

.delete-dialog-icon {
  flex-shrink: 0;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 50%;
  background: #fef2f2;
  color: #dc2626;
  display: flex;
  align-items: center;
  justify-content: center;
}

.delete-dialog-msg {
  color: var(--color-ink-muted, #6b7280);
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
  line-height: 1.5;
}

.delete-dialog-warning {
  padding: 0.75rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  color: #991b1b;
  line-height: 1.4;
}

.delete-dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border, #e5e7eb);
}

.admin-btn-delete {
  padding: 0.5rem 1rem;
  background: #dc2626;
  color: #fff;
  border: none;
  border-radius: var(--radius-sm, 0.375rem);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}

.admin-btn-delete:hover:not(:disabled) {
  background: #b91c1c;
}

.admin-btn-delete:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
