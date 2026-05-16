<script setup>
import { onMounted, ref } from 'vue'
import { createDepartment, deleteDepartment, getDepartments, updateDepartment } from '../services/api'
import { getApiError, pick, toDateInput, toNullableInt, toNullableString } from '../components/utils/crud'
import { useToast } from '../composables/useToast'
import Pagination from '../components/Pagination.vue'
import SearchFilter from '../components/SearchFilter.vue'
import ConfirmDeleteDialog from '../components/ConfirmDeleteDialog.vue'

const toast = useToast()

const departments = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingDepartmentId = ref(null)
const currentPage = ref(1)
const pageSize = 100
const searchQuery = ref('')

const selectedIds = ref(new Set())
const selectAll = () => {
  if (selectedIds.value.size === departments.value.length) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(departments.value.map(d => d.department_id))
  }
}
const toggleSelect = (id) => {
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id); else next.add(id)
  selectedIds.value = next
}

const showDeleteDialog = ref(false)
const deletingDeptId = ref(null)
const deleteDeptName = ref('')
const deleting = ref(false)

const defaultForm = () => ({
  department_code: '',
  department_name: '',
  description: '',
  head_faculty_id: '',
  parent_department_id: '',
  building: '',
  phone: '',
  email: '',
  website_url: '',
  established_date: '',
  is_active: true,
})

const form = ref(defaultForm())

const loadDepartments = async () => {
  loading.value = true
  error.value = ''
  try {
    const skip = (currentPage.value - 1) * pageSize
    const response = await getDepartments(skip, pageSize, searchQuery.value)
    departments.value = response.data.departments
    total.value = response.data.total
  } catch (err) {
    error.value = getApiError(err, 'Failed to load departments')
  } finally {
    loading.value = false
  }
}

const goToPage = (page) => {
  selectedIds.value = new Set()
  currentPage.value = page
  loadDepartments()
}

const onSearch = (val) => {
  selectedIds.value = new Set()
  searchQuery.value = val
  currentPage.value = 1
  loadDepartments()
}

const openCreate = () => {
  editingDepartmentId.value = null
  form.value = defaultForm()
  showModal.value = true
}

const openEdit = (department) => {
  editingDepartmentId.value = department.department_id
  form.value = {
    department_code: department.department_code || '',
    department_name: department.department_name || '',
    description: department.description || '',
    head_faculty_id: department.head_faculty_id || '',
    parent_department_id: department.parent_department_id ?? '',
    building: department.building || '',
    phone: department.phone || '',
    email: department.email || '',
    website_url: department.website_url || '',
    established_date: toDateInput(department.established_date),
    is_active: department.is_active ?? true,
  }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingDepartmentId.value = null
}

const buildPayload = () => ({
  ...pick(form.value, ['department_code', 'department_name', 'is_active']),
  description: toNullableString(form.value.description),
  head_faculty_id: toNullableString(form.value.head_faculty_id),
  parent_department_id: toNullableInt(form.value.parent_department_id),
  building: toNullableString(form.value.building),
  phone: toNullableString(form.value.phone),
  email: toNullableString(form.value.email),
  website_url: toNullableString(form.value.website_url),
  established_date: toNullableString(form.value.established_date),
})

const saveDepartment = async () => {
  saving.value = true
  error.value = ''
  try {
    const payload = buildPayload()
    if (editingDepartmentId.value) {
      await updateDepartment(editingDepartmentId.value, payload)
    } else {
      await createDepartment(payload)
    }
    closeModal()
    currentPage.value = 1
    await loadDepartments()
  } catch (err) {
    error.value = getApiError(err, 'Failed to save department')
  } finally {
    saving.value = false
  }
}

const confirmDeleteDepartment = (departmentId, deptName) => {
  deletingDeptId.value = departmentId
  deleteDeptName.value = deptName
  showDeleteDialog.value = true
}

const executeDeleteDepartment = async () => {
  deleting.value = true
  try {
    await deleteDepartment(deletingDeptId.value)
    showDeleteDialog.value = false
    currentPage.value = 1
    await loadDepartments()
    toast.success('Department deleted successfully')
  } catch (err) {
    toast.error(getApiError(err, 'Failed to delete department'))
    showDeleteDialog.value = false
  } finally {
    deleting.value = false
  }
}

const bulkDeleting = ref(false)
const showBulkDeleteDialog = ref(false)
const deleteSelectedDepartments = async () => {
  bulkDeleting.value = true
  showBulkDeleteDialog.value = false
  const ids = [...selectedIds.value]
  let successCount = 0
  let failCount = 0
  for (const id of ids) {
    try {
      await deleteDepartment(id)
      successCount++
    } catch {
      failCount++
    }
  }
  selectedIds.value = new Set()
  currentPage.value = 1
  await loadDepartments()
  if (failCount > 0) {
    toast.warning(`Deleted ${successCount} department(s), ${failCount} failed`)
  } else {
    toast.success(`Deleted ${successCount} department(s)`)
  }
  bulkDeleting.value = false
}

onMounted(loadDepartments)
</script>

<template>
  <div>
    <div class="admin-page-header">
      <h1>Departments</h1>
      <button class="admin-btn-add" @click="openCreate">+ Add Department</button>
    </div>

    <div v-if="error" class="admin-error">{{ error }}</div>

    <div v-if="loading" class="admin-loading">Loading departments...</div>

    <div v-else class="admin-table-card">
      <div class="px-4 pt-3 pb-2 border-b border-border-light">
        <SearchFilter v-model="searchQuery" @search="onSearch" placeholder="Search departments..." />
      </div>
      <div class="admin-record-count">{{ total }} department(s)</div>
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
              <input type="checkbox" :checked="departments.length > 0 && selectedIds.size === departments.length" @change="selectAll" />
            </th>
            <th>Code</th>
            <th>Name</th>
            <th>Building</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="dept in departments" :key="dept.department_id" :class="{ 'row-selected': selectedIds.has(dept.department_id) }">
            <td class="td-checkbox">
              <input type="checkbox" :checked="selectedIds.has(dept.department_id)" @change="toggleSelect(dept.department_id)" />
            </td>
            <td class="cell-primary">{{ dept.department_code }}</td>
            <td class="font-medium text-ink">{{ dept.department_name }}</td>
            <td>{{ dept.building || '-' }}</td>
            <td>
              <span class="admin-badge" :class="dept.is_active ? 'admin-badge-active' : 'admin-badge-inactive'">
                {{ dept.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td>
              <button class="admin-action-btn admin-action-edit" @click="openEdit(dept)">Edit</button>
              <button class="admin-action-btn admin-action-delete"
                @click="confirmDeleteDepartment(dept.department_id, dept.department_name)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <Pagination :current-page="currentPage" :total-items="total" :page-size="pageSize" @page-change="goToPage" />
    </div>

    <div v-if="showModal" class="admin-modal-overlay">
      <div class="admin-modal admin-modal-lg">
        <h2>{{ editingDepartmentId ? 'Edit Department' : 'Create Department' }}</h2>
        <form class="admin-form-grid" @submit.prevent="saveDepartment">
          <div>
            <label class="form-label">Department Code</label>
            <input v-model="form.department_code" required />
          </div>
          <div>
            <label class="form-label">Department Name</label>
            <input v-model="form.department_name" required />
          </div>
          <div>
            <label class="form-label">Building</label>
            <input v-model="form.building" />
          </div>
          <div>
            <label class="form-label">Parent Department ID</label>
            <input v-model="form.parent_department_id" type="number" min="1" />
          </div>
          <div>
            <label class="form-label">Email</label>
            <input v-model="form.email" type="email" />
          </div>
          <div>
            <label class="form-label">Phone</label>
            <input v-model="form.phone" />
          </div>
          <div>
            <label class="form-label">Website URL</label>
            <input v-model="form.website_url" />
          </div>
          <div>
            <label class="form-label">Established Date</label>
            <input v-model="form.established_date" type="date" />
          </div>
          <div>
            <label class="form-label">Head Faculty ID</label>
            <input v-model="form.head_faculty_id" />
          </div>
          <label class="admin-checkbox-row">
            <input v-model="form.is_active" type="checkbox" />
            Active
          </label>
          <div class="col-span-full">
            <label class="form-label">Description</label>
            <textarea v-model="form.description" rows="3" />
          </div>
          <div class="admin-form-actions">
            <button type="button" class="admin-btn-cancel" @click="closeModal">Cancel</button>
            <button :disabled="saving" type="submit" class="admin-btn-save">
              {{ saving ? 'Saving...' : 'Save' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <ConfirmDeleteDialog
      :show="showDeleteDialog"
      title="Delete Department"
      :item-name="deleteDeptName"
      :deleting="deleting"
      @confirm="executeDeleteDepartment"
      @cancel="showDeleteDialog = false"
    />

    <div v-if="showBulkDeleteDialog" class="admin-modal-overlay" @click.self="showBulkDeleteDialog = false">
      <div class="admin-modal admin-modal-sm">
        <h2>Delete {{ selectedIds.size }} Department(s)</h2>
        <p class="text-ink-muted mb-4">Are you sure you want to delete {{ selectedIds.size }} selected department(s)? All associated data will be permanently deleted.</p>
        <div class="admin-form-actions">
          <button type="button" class="admin-btn-cancel" @click="showBulkDeleteDialog = false">Cancel</button>
          <button :disabled="bulkDeleting" class="admin-btn-delete-selected" @click="deleteSelectedDepartments">
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
