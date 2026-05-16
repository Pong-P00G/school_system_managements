<script setup>
import { onMounted, ref } from 'vue'
import { createTerm, deleteTerm, getTerms, updateTerm } from '../services/api'
import { getApiError, pick, toDateInput, toNullableString } from '../components/utils/crud'
import { useToast } from '../composables/useToast'
import Pagination from '../components/Pagination.vue'
import SearchFilter from '../components/SearchFilter.vue'
import ConfirmDeleteDialog from '../components/ConfirmDeleteDialog.vue'

const toast = useToast()

const terms = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingTermId = ref(null)
const currentPage = ref(1)
const pageSize = 100
const searchQuery = ref('')

const selectedIds = ref(new Set())
const selectAll = () => {
  if (selectedIds.value.size === terms.value.length) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(terms.value.map(t => t.term_id))
  }
}
const toggleSelect = (id) => {
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id); else next.add(id)
  selectedIds.value = next
}

const showDeleteDialog = ref(false)
const deletingTermId = ref(null)
const deleteTermName = ref('')
const deleting = ref(false)

const defaultForm = () => ({
  term_name: '',
  term_code: '',
  academic_year: `${new Date().getFullYear()}-${new Date().getFullYear() + 1}`,
  term_type: 'fall',
  start_date: '',
  end_date: '',
  registration_start_date: '',
  registration_end_date: '',
  add_drop_deadline: '',
  withdrawal_deadline: '',
  final_exam_start_date: '',
  final_exam_end_date: '',
  status: 'upcoming',
})

const form = ref(defaultForm())

const loadTerms = async () => {
  loading.value = true
  error.value = ''
  try {
    const skip = (currentPage.value - 1) * pageSize
    const response = await getTerms(skip, pageSize, null, null, null, searchQuery.value)
    terms.value = response.data.terms
    total.value = response.data.total
  } catch (err) {
    error.value = getApiError(err, 'Failed to load academic terms')
  } finally {
    loading.value = false
  }
}

const goToPage = (page) => {
  selectedIds.value = new Set()
  currentPage.value = page
  loadTerms()
}

const onSearch = (val) => {
  selectedIds.value = new Set()
  searchQuery.value = val
  currentPage.value = 1
  loadTerms()
}

const openCreate = () => { editingTermId.value = null; form.value = defaultForm(); showModal.value = true }

const openEdit = (term) => {
  editingTermId.value = term.term_id
  form.value = {
    term_name: term.term_name || '', term_code: term.term_code || '',
    academic_year: term.academic_year || '', term_type: term.term_type || 'fall',
    start_date: toDateInput(term.start_date), end_date: toDateInput(term.end_date),
    registration_start_date: toDateInput(term.registration_start_date),
    registration_end_date: toDateInput(term.registration_end_date),
    add_drop_deadline: toDateInput(term.add_drop_deadline),
    withdrawal_deadline: toDateInput(term.withdrawal_deadline),
    final_exam_start_date: toDateInput(term.final_exam_start_date),
    final_exam_end_date: toDateInput(term.final_exam_end_date),
    status: term.status || 'upcoming',
  }
  showModal.value = true
}

const closeModal = () => { showModal.value = false; editingTermId.value = null }

const buildPayload = () => ({
  ...pick(form.value, ['term_name', 'term_code', 'academic_year', 'term_type', 'start_date', 'end_date', 'status']),
  registration_start_date: toNullableString(form.value.registration_start_date),
  registration_end_date: toNullableString(form.value.registration_end_date),
  add_drop_deadline: toNullableString(form.value.add_drop_deadline),
  withdrawal_deadline: toNullableString(form.value.withdrawal_deadline),
  final_exam_start_date: toNullableString(form.value.final_exam_start_date),
  final_exam_end_date: toNullableString(form.value.final_exam_end_date),
})

const saveTerm = async () => {
  saving.value = true; error.value = ''
  try {
    const payload = buildPayload()
    if (editingTermId.value) { await updateTerm(editingTermId.value, payload) }
    else { await createTerm(payload) }
    closeModal(); currentPage.value = 1; await loadTerms()
  } catch (err) { error.value = getApiError(err, 'Failed to save academic term') }
  finally { saving.value = false }
}

const confirmDeleteTerm = (termId, termName) => {
  deletingTermId.value = termId
  deleteTermName.value = termName
  showDeleteDialog.value = true
}

const executeDeleteTerm = async () => {
  deleting.value = true
  try {
    await deleteTerm(deletingTermId.value)
    showDeleteDialog.value = false
    currentPage.value = 1
    await loadTerms()
    toast.success('Term deleted successfully')
  } catch (err) {
    toast.error(getApiError(err, 'Failed to delete academic term'))
    showDeleteDialog.value = false
  } finally {
    deleting.value = false
  }
}


const bulkDeleting = ref(false)
const showBulkDeleteDialog = ref(false)
const deleteSelectedTerms = async () => {
  bulkDeleting.value = true
  showBulkDeleteDialog.value = false
  const ids = [...selectedIds.value]
  let successCount = 0
  let failCount = 0
  for (const id of ids) {
    try {
      await deleteTerm(id)
      successCount++
    } catch {
      failCount++
    }
  }
  selectedIds.value = new Set()
  currentPage.value = 1
  await loadTerms()
  if (failCount > 0) {
    toast.warning(`Deleted ${successCount} term(s), ${failCount} failed`)
  } else {
    toast.success(`Deleted ${successCount} term(s)`)
  }
  bulkDeleting.value = false
}

onMounted(loadTerms)
</script>

<template>
  <div>
    <div class="admin-page-header">
      <h1>Academic Terms</h1>
      <button class="admin-btn-add" @click="openCreate">+ Add Term</button>
    </div>

    <div v-if="error" class="admin-error">{{ error }}</div>
    <div v-if="loading" class="admin-loading">Loading terms...</div>

    <div v-else class="admin-table-card">
      <div class="px-4 pt-3 pb-2 border-b border-border-light">
        <SearchFilter v-model="searchQuery" @search="onSearch" placeholder="Search terms..." />
      </div>
      <div class="admin-record-count">{{ total }} term(s)</div>
      <div v-if="selectedIds.size > 0" class="admin-bulk-actions">
        <span class="bulk-count">{{ selectedIds.size }} selected</span>
        <button class="admin-btn-delete-selected" :disabled="bulkDeleting" @click="showBulkDeleteDialog = true">
          {{ bulkDeleting ? 'Deleting...' : 'Delete Selected' }}
        </button>
      </div>
      <table class="admin-table">
        <thead>
          <tr>
            <th class="th-checkbox">
              <input type="checkbox" :checked="terms.length > 0 && selectedIds.size === terms.length" @change="selectAll" />
            </th>
            <th>Term</th>
            <th>Code</th>
            <th>Academic Year</th>
            <th>Dates</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="term in terms" :key="term.term_id" :class="{ 'row-selected': selectedIds.has(term.term_id) }">
            <td class="td-checkbox">
              <input type="checkbox" :checked="selectedIds.has(term.term_id)" @change="toggleSelect(term.term_id)" />
            </td>
            <td class="cell-primary">{{ term.term_name }}</td>
            <td>{{ term.term_code }}</td>
            <td>{{ term.academic_year }}</td>
            <td>{{ term.start_date }} to {{ term.end_date }}</td>
            <td>{{ term.status }}</td>
            <td>
              <button class="admin-action-btn admin-action-edit" @click="openEdit(term)">Edit</button>
              <button class="admin-action-btn admin-action-delete" @click="confirmDeleteTerm(term.term_id, term.term_name)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <Pagination :current-page="currentPage" :total-items="total" :page-size="pageSize" @page-change="goToPage" />
    </div>

    <div v-if="showModal" class="admin-modal-overlay">
      <div class="admin-modal admin-modal-lg">
        <h2>{{ editingTermId ? 'Edit Term' : 'Create Term' }}</h2>
        <form class="admin-form-grid" @submit.prevent="saveTerm">
          <div><label class="form-label">Term Name</label><input v-model="form.term_name" required /></div>
          <div><label class="form-label">Term Code</label><input v-model="form.term_code" required /></div>
          <div><label class="form-label">Academic Year</label><input v-model="form.academic_year" required /></div>
          <div>
            <label class="form-label">Term Type</label>
            <select v-model="form.term_type">
              <option value="fall">Fall</option>
              <option value="spring">Spring</option>
              <option value="summer">Summer</option>
              <option value="winter">Winter</option>
            </select>
          </div>
          <div><label class="form-label">Start Date</label><input v-model="form.start_date" type="date" required />
          </div>
          <div><label class="form-label">End Date</label><input v-model="form.end_date" type="date" required /></div>
          <div><label class="form-label">Registration Start</label><input v-model="form.registration_start_date"
              type="date" /></div>
          <div><label class="form-label">Registration End</label><input v-model="form.registration_end_date"
              type="date" /></div>
          <div><label class="form-label">Add/Drop Deadline</label><input v-model="form.add_drop_deadline" type="date" />
          </div>
          <div><label class="form-label">Withdrawal Deadline</label><input v-model="form.withdrawal_deadline"
              type="date" /></div>
          <div><label class="form-label">Final Exam Start</label><input v-model="form.final_exam_start_date"
              type="date" /></div>
          <div><label class="form-label">Final Exam End</label><input v-model="form.final_exam_end_date" type="date" />
          </div>
          <div>
            <label class="form-label">Status</label>
            <select v-model="form.status">
              <option value="upcoming">Upcoming</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          <div class="admin-form-actions">
            <button type="button" class="admin-btn-cancel" @click="closeModal">Cancel</button>
            <button :disabled="saving" type="submit" class="admin-btn-save">{{ saving ? 'Saving...' : 'Save' }}</button>
          </div>
        </form>
      </div>
    </div>

    <ConfirmDeleteDialog
      :show="showDeleteDialog"
      title="Delete Term"
      :item-name="deleteTermName"
      :deleting="deleting"
      @confirm="executeDeleteTerm"
      @cancel="showDeleteDialog = false"
    />

    <div v-if="showBulkDeleteDialog" class="admin-modal-overlay" @click.self="showBulkDeleteDialog = false">
      <div class="admin-modal admin-modal-sm">
        <h2>Delete {{ selectedIds.size }} Term(s)</h2>
        <p class="text-ink-muted mb-4">Are you sure you want to delete {{ selectedIds.size }} selected term(s)? This action cannot be undone. All associated data will also be permanently deleted.</p>
        <div class="admin-form-actions">
          <button type="button" class="admin-btn-cancel" @click="showBulkDeleteDialog = false">Cancel</button>
          <button :disabled="bulkDeleting" class="admin-btn-delete-selected" @click="deleteSelectedTerms">
            {{ bulkDeleting ? 'Deleting...' : 'Delete All' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.th-checkbox, .td-checkbox {
  width: 40px;
  text-align: center;
  vertical-align: middle;
}
.th-checkbox input, .td-checkbox input {
  width: 16px;
  height: 16px;
  cursor: pointer;
}
.row-selected {
  background-color: rgba(59, 130, 246, 0.05);
}
.admin-bulk-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: #fef2f2;
  border-bottom: 1px solid #fecaca;
}
.bulk-count {
  font-size: 14px;
  font-weight: 600;
  color: #b91c1c;
}
.admin-btn-delete-selected {
  padding: 6px 16px;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.admin-btn-delete-selected:hover:not(:disabled) {
  background: #b91c1c;
}
.admin-btn-delete-selected:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
