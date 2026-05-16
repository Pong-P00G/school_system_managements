<script setup>
import { onMounted, ref } from 'vue'
import { createStaff, deleteStaff, getDepartments, getStaff, getUsers, updateStaff } from '../services/api'
import { getApiError, pick, toDateInput, toNullableInt, toNullableString } from '../components/utils/crud'
import { useToast } from '../composables/useToast'
import Pagination from '../components/Pagination.vue'
import SearchFilter from '../components/SearchFilter.vue'
import ConfirmDeleteDialog from '../components/ConfirmDeleteDialog.vue'

const toast = useToast()

const staff = ref([])
const departments = ref([])
const users = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingStaffId = ref(null)
const currentPage = ref(1)
const pageSize = 100
const searchQuery = ref('')

const selectedIds = ref(new Set())
const selectAll = () => {
  if (selectedIds.value.size === staff.value.length) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(staff.value.map(s => s.staff_id))
  }
}
const toggleSelect = (id) => {
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id); else next.add(id)
  selectedIds.value = next
}

const showDeleteDialog = ref(false)
const deletingStaffId = ref(null)
const deleteStaffName = ref('')
const deleting = ref(false)

const defaultForm = () => ({
  employee_number: '', user_id: '', department_id: '',
  hire_date: new Date().toISOString().slice(0, 10), termination_date: '',
  job_title: '', job_category: 'administrative', employment_type: 'full-time',
  employment_status: 'active', office_room_id: '', supervisor_id: '', salary_grade: '',
})

const form = ref(defaultForm())

const loadStaff = async () => {
  loading.value = true; error.value = ''
  try {
    const skip = (currentPage.value - 1) * pageSize
    const [staffRes, departmentsRes, usersRes] = await Promise.all([
      getStaff(skip, pageSize, null, null, null, searchQuery.value), getDepartments(0, 200), getUsers(0, 200),
    ])
    staff.value = staffRes.data.staff; total.value = staffRes.data.total
    departments.value = departmentsRes.data.departments; users.value = usersRes.data.users
  } catch (err) { error.value = getApiError(err, 'Failed to load staff') }
  finally { loading.value = false }
}

const goToPage = (page) => {
  selectedIds.value = new Set()
  currentPage.value = page
  loadStaff()
}

const onSearch = (val) => {
  selectedIds.value = new Set()
  searchQuery.value = val
  currentPage.value = 1
  loadStaff()
}

const openCreate = () => { editingStaffId.value = null; form.value = defaultForm(); showModal.value = true }

const openEdit = (member) => {
  editingStaffId.value = member.staff_id
  form.value = {
    employee_number: member.employee_number || '',
    user_id: String(member.staff_id || ''), department_id: member.department_id ?? '',
    hire_date: toDateInput(member.hire_date), termination_date: toDateInput(member.termination_date),
    job_title: member.job_title || '', job_category: member.job_category || 'administrative',
    employment_type: member.employment_type || 'full-time',
    employment_status: member.employment_status || 'active',
    office_room_id: member.office_room_id ?? '', supervisor_id: member.supervisor_id || '',
    salary_grade: member.salary_grade || '',
  }
  showModal.value = true
}

const closeModal = () => { showModal.value = false; editingStaffId.value = null }

const buildCreatePayload = () => ({
  ...pick(form.value, ['employee_number', 'job_title', 'job_category', 'employment_type', 'employment_status']),
  user_id: String(form.value.user_id), department_id: toNullableInt(form.value.department_id),
  hire_date: form.value.hire_date, termination_date: toNullableString(form.value.termination_date),
  office_room_id: toNullableInt(form.value.office_room_id),
  supervisor_id: toNullableString(form.value.supervisor_id), salary_grade: toNullableString(form.value.salary_grade),
})

const buildUpdatePayload = () => ({
  ...pick(form.value, ['employee_number', 'job_title', 'job_category', 'employment_type', 'employment_status']),
  department_id: toNullableInt(form.value.department_id), hire_date: form.value.hire_date,
  termination_date: toNullableString(form.value.termination_date),
  office_room_id: toNullableInt(form.value.office_room_id),
  supervisor_id: toNullableString(form.value.supervisor_id), salary_grade: toNullableString(form.value.salary_grade),
})

const saveStaff = async () => {
  saving.value = true; error.value = ''
  try {
    if (editingStaffId.value) { await updateStaff(editingStaffId.value, buildUpdatePayload()) }
    else { await createStaff(buildCreatePayload()) }
    closeModal(); currentPage.value = 1; await loadStaff()
  } catch (err) { error.value = getApiError(err, 'Failed to save staff member') }
  finally { saving.value = false }
}

const confirmDeleteStaff = (staffId, name) => {
  deletingStaffId.value = staffId
  deleteStaffName.value = name
  showDeleteDialog.value = true
}

const executeDeleteStaff = async () => {
  deleting.value = true
  try {
    await deleteStaff(deletingStaffId.value)
    showDeleteDialog.value = false
    currentPage.value = 1
    await loadStaff()
    toast.success('Staff deleted successfully')
  } catch (err) {
    toast.error(getApiError(err, 'Failed to delete staff member'))
    showDeleteDialog.value = false
  } finally {
    deleting.value = false
  }
}


const bulkDeleting = ref(false)
const showBulkDeleteDialog = ref(false)
const deleteSelectedStaff = async () => {
  bulkDeleting.value = true
  showBulkDeleteDialog.value = false
  const ids = [...selectedIds.value]
  let successCount = 0
  let failCount = 0
  for (const id of ids) {
    try {
      await deleteStaff(id)
      successCount++
    } catch {
      failCount++
    }
  }
  selectedIds.value = new Set()
  currentPage.value = 1
  await loadStaff()
  if (failCount > 0) {
    toast.warning(`Deleted ${successCount} staff member(s), ${failCount} failed`)
  } else {
    toast.success(`Deleted ${successCount} staff member(s)`)
  }
  bulkDeleting.value = false
}

const departmentNameById = (departmentId) => {
  const match = departments.value.find((department) => department.department_id === departmentId)
  return match ? match.department_name : departmentId ? `ID ${departmentId}` : '-'
}

const userLabelById = (userId) => {
  const match = users.value.find((user) => user.user_id === userId)
  if (!match) return userId
  return `${match.username} (${match.email})`
}

onMounted(loadStaff)
</script>

<template>
  <div>
    <div class="admin-page-header">
      <h1>Staff</h1>
      <button class="admin-btn-add" @click="openCreate">+ Add Staff</button>
    </div>

    <div v-if="error" class="admin-error">{{ error }}</div>
    <div v-if="loading" class="admin-loading">Loading staff...</div>

    <div v-else class="admin-table-card">
      <div class="px-4 pt-3 pb-2 border-b border-border-light">
        <SearchFilter v-model="searchQuery" @search="onSearch" placeholder="Search staff..." />
      </div>
      <div class="admin-record-count">{{ total }} staff member(s)</div>
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
              <input type="checkbox" :checked="staff.length > 0 && selectedIds.size === staff.length" @change="selectAll" />
            </th>
            <th>Employee</th>
            <th>Job Title</th>
            <th>Department</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="member in staff" :key="member.staff_id" :class="{ 'row-selected': selectedIds.has(member.staff_id) }">
            <td class="td-checkbox">
              <input type="checkbox" :checked="selectedIds.has(member.staff_id)" @change="toggleSelect(member.staff_id)" />
            </td>
            <td class="cell-primary">{{ member.employee_number }}</td>
            <td>{{ member.job_title }}</td>
            <td>{{ departmentNameById(member.department_id) }}</td>
            <td>{{ member.employment_status }}</td>
            <td>
              <button class="admin-action-btn admin-action-edit" @click="openEdit(member)">Edit</button>
              <button class="admin-action-btn admin-action-delete" @click="confirmDeleteStaff(member.staff_id, member.employee_number)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <Pagination :current-page="currentPage" :total-items="total" :page-size="pageSize" @page-change="goToPage" />
    </div>

    <div v-if="showModal" class="admin-modal-overlay">
      <div class="admin-modal admin-modal-lg">
        <h2>{{ editingStaffId ? 'Edit Staff Member' : 'Create Staff Member' }}</h2>
        <form class="admin-form-grid" @submit.prevent="saveStaff">
          <div><label class="form-label">Employee Number</label><input v-model="form.employee_number" required /></div>
          <div>
            <label class="form-label">User</label>
            <select v-model="form.user_id" :disabled="Boolean(editingStaffId)" required>
              <option value="" disabled>Select user</option>
              <option v-for="user in users" :key="user.user_id" :value="String(user.user_id)">{{
                userLabelById(user.user_id) }}</option>
            </select>
          </div>
          <div>
            <label class="form-label">Department</label>
            <select v-model="form.department_id">
              <option value="">No department</option>
              <option v-for="department in departments" :key="department.department_id"
                :value="String(department.department_id)">{{ department.department_code }} - {{
                  department.department_name }}</option>
            </select>
          </div>
          <div><label class="form-label">Hire Date</label><input v-model="form.hire_date" type="date" required /></div>
          <div><label class="form-label">Termination Date</label><input v-model="form.termination_date" type="date" />
          </div>
          <div><label class="form-label">Job Title</label><input v-model="form.job_title" required /></div>
          <div>
            <label class="form-label">Job Category</label>
            <select v-model="form.job_category">
              <option value="administrative">Administrative</option>
              <option value="technical">Technical</option>
              <option value="support">Support</option>
              <option value="maintenance">Maintenance</option>
            </select>
          </div>
          <div>
            <label class="form-label">Employment Type</label>
            <select v-model="form.employment_type">
              <option value="full-time">Full-Time</option>
              <option value="part-time">Part-Time</option>
              <option value="temporary">Temporary</option>
            </select>
          </div>
          <div>
            <label class="form-label">Employment Status</label>
            <select v-model="form.employment_status">
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="on-leave">On Leave</option>
            </select>
          </div>
          <div><label class="form-label">Office Room ID</label><input v-model="form.office_room_id" type="number"
              min="1" /></div>
          <div><label class="form-label">Supervisor ID</label><input v-model="form.supervisor_id" /></div>
          <div><label class="form-label">Salary Grade</label><input v-model="form.salary_grade" /></div>
          <div class="admin-form-actions">
            <button type="button" class="admin-btn-cancel" @click="closeModal">Cancel</button>
            <button :disabled="saving" type="submit" class="admin-btn-save">{{ saving ? 'Saving...' : 'Save' }}</button>
          </div>
        </form>
      </div>
    </div>

    <ConfirmDeleteDialog
      :show="showDeleteDialog"
      title="Delete Staff"
      :item-name="deleteStaffName"
      :deleting="deleting"
      @confirm="executeDeleteStaff"
      @cancel="showDeleteDialog = false"
    />

    <div v-if="showBulkDeleteDialog" class="admin-modal-overlay" @click.self="showBulkDeleteDialog = false">
      <div class="admin-modal admin-modal-sm">
        <h2>Delete {{ selectedIds.size }} Staff Member(s)</h2>
        <p class="text-ink-muted mb-4">Are you sure you want to delete {{ selectedIds.size }} selected staff member(s)? This action cannot be undone. All associated data will also be permanently deleted.</p>
        <div class="admin-form-actions">
          <button type="button" class="admin-btn-cancel" @click="showBulkDeleteDialog = false">Cancel</button>
          <button :disabled="bulkDeleting" class="admin-btn-delete-selected" @click="deleteSelectedStaff">
            {{ bulkDeleting ? 'Deleting...' : 'Delete All' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>


