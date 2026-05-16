<script setup>
import { onMounted, ref } from 'vue'
import { createFaculty, deleteFaculty, getDepartments, getFaculty, getUsers, updateFaculty } from '../services/api'
import { getApiError, pick, toDateInput, toNullableInt, toNullableString } from '../components/utils/crud'
import { useToast } from '../composables/useToast'
import Pagination from '../components/Pagination.vue'
import SearchFilter from '../components/SearchFilter.vue'
import ConfirmDeleteDialog from '../components/ConfirmDeleteDialog.vue'
import { getFacultySections } from '../services/api'

const toast = useToast()

const faculty = ref([])
const departments = ref([])
const users = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingFacultyId = ref(null)
const currentPage = ref(1)
const pageSize = 100
const searchQuery = ref('')

const selectedIds = ref(new Set())
const selectAll = () => {
  if (selectedIds.value.size === faculty.value.length) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(faculty.value.map(m => m.faculty_id))
  }
}
const toggleSelect = (id) => {
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id); else next.add(id)
  selectedIds.value = next
}

const showDeleteDialog = ref(false)
const deletingFacultyId = ref(null)
const deleteFacultyName = ref('')
const deleting = ref(false)

const defaultForm = () => ({
  employee_number: '', user_id: '', department_id: '',
  hire_date: new Date().toISOString().slice(0, 10), termination_date: '',
  faculty_rank: 'Assistant Professor', tenure_status: 'tenure-track',
  employment_type: 'full-time', employment_status: 'active',
  office_room_id: '', office_hours: '', research_interests: '',
})

const form = ref(defaultForm())

const loadFaculty = async () => {
  loading.value = true; error.value = ''
  try {
    const skip = (currentPage.value - 1) * pageSize
    const [facultyRes, departmentsRes, usersRes] = await Promise.all([
      getFaculty(skip, pageSize, null, null, null, searchQuery.value), getDepartments(0, 200), getUsers(0, 200),
    ])
    faculty.value = facultyRes.data.faculty; total.value = facultyRes.data.total
    departments.value = departmentsRes.data.departments; users.value = usersRes.data.users
  } catch (err) { error.value = getApiError(err, 'Failed to load faculty') }
  finally { loading.value = false }
}

const goToPage = (page) => {
  selectedIds.value = new Set()
  currentPage.value = page
  loadFaculty()
}

const onSearch = (val) => {
  selectedIds.value = new Set()
  searchQuery.value = val
  currentPage.value = 1
  loadFaculty()
}

const openCreate = () => { editingFacultyId.value = null; form.value = defaultForm(); showModal.value = true }

const openEdit = (member) => {
  editingFacultyId.value = member.faculty_id
  form.value = {
    employee_number: member.employee_number || '',
    user_id: String(member.faculty_id || ''),
    department_id: String(member.department_id || ''),
    hire_date: toDateInput(member.hire_date), termination_date: toDateInput(member.termination_date),
    faculty_rank: member.faculty_rank || 'Assistant Professor',
    tenure_status: member.tenure_status || 'tenure-track',
    employment_type: member.employment_type || 'full-time',
    employment_status: member.employment_status || 'active',
    office_room_id: member.office_room_id ?? '',
    office_hours: member.office_hours || '', research_interests: member.research_interests || '',
  }
  showModal.value = true
}

const closeModal = () => { showModal.value = false; editingFacultyId.value = null }

const buildCreatePayload = () => ({
  ...pick(form.value, ['employee_number', 'faculty_rank', 'tenure_status', 'employment_type', 'employment_status']),
  user_id: String(form.value.user_id), department_id: Number(form.value.department_id),
  hire_date: form.value.hire_date, termination_date: toNullableString(form.value.termination_date),
  office_room_id: toNullableInt(form.value.office_room_id),
  office_hours: toNullableString(form.value.office_hours),
  research_interests: toNullableString(form.value.research_interests),
})

const buildUpdatePayload = () => ({
  ...pick(form.value, ['employee_number', 'faculty_rank', 'tenure_status', 'employment_type', 'employment_status']),
  department_id: Number(form.value.department_id), hire_date: form.value.hire_date,
  termination_date: toNullableString(form.value.termination_date),
  office_room_id: toNullableInt(form.value.office_room_id),
  office_hours: toNullableString(form.value.office_hours),
  research_interests: toNullableString(form.value.research_interests),
})

const saveFaculty = async () => {
  saving.value = true; error.value = ''
  try {
    if (editingFacultyId.value) { await updateFaculty(editingFacultyId.value, buildUpdatePayload()) }
    else { await createFaculty(buildCreatePayload()) }
    closeModal(); currentPage.value = 1; await loadFaculty()
  } catch (err) { error.value = getApiError(err, 'Failed to save faculty') }
  finally { saving.value = false }
}

const confirmDeleteFaculty = (facultyId, name) => {
  deletingFacultyId.value = facultyId
  deleteFacultyName.value = name
  showDeleteDialog.value = true
}

const executeDeleteFaculty = async () => {
  deleting.value = true
  try {
    await deleteFaculty(deletingFacultyId.value)
    showDeleteDialog.value = false
    currentPage.value = 1
    await loadFaculty()
    toast.success('Faculty deleted successfully')
  } catch (err) {
    toast.error(getApiError(err, 'Failed to delete faculty'))
    showDeleteDialog.value = false
  } finally {
    deleting.value = false
  }
}


const bulkDeleting = ref(false)
const showBulkDeleteDialog = ref(false)
const deleteSelectedFaculty = async () => {
  bulkDeleting.value = true
  showBulkDeleteDialog.value = false
  const ids = [...selectedIds.value]
  let successCount = 0
  let failCount = 0
  for (const id of ids) {
    try {
      await deleteFaculty(id)
      successCount++
    } catch {
      failCount++
    }
  }
  selectedIds.value = new Set()
  currentPage.value = 1
  await loadFaculty()
  if (failCount > 0) {
    toast.warning(`Deleted ${successCount} faculty member(s), ${failCount} failed`)
  } else {
    toast.success(`Deleted ${successCount} faculty member(s)`)
  }
  bulkDeleting.value = false
}

const departmentNameById = (departmentId) => {
  const match = departments.value.find((department) => department.department_id === departmentId)
  return match ? match.department_name : `ID ${departmentId}`
}

const userLabelById = (userId) => {
  const match = users.value.find((user) => user.user_id === userId)
  if (!match) return userId
  return `${match.username} (${match.email})`
}

import { useRouter } from 'vue-router'
const router = useRouter()
const viewDetails = (id) => { router.push(`/faculty/${id}`) }

onMounted(loadFaculty)
</script>

<template>
  <div>
    <div class="admin-page-header">
      <h1>Faculty Management</h1>
      <button class="admin-btn-add" @click="openCreate">+ Add Faculty</button>
    </div>

    <div v-if="error" class="admin-error">{{ error }}</div>
    <div v-if="loading" class="admin-loading">Loading faculty...</div>

    <div v-else class="admin-table-card">
      <div class="px-4 pt-3 pb-2 border-b border-border-light">
        <SearchFilter v-model="searchQuery" @search="onSearch" placeholder="Search faculty..." />
      </div>
      <div class="admin-record-count">{{ total }} faculty member(s)</div>
      <div v-if="selectedIds.size > 0" class="admin-bulk-actions">
        <span class="bulk-count">{{ selectedIds.size }} selected</span>
        <button class="admin-btn-delete-selected" :disabled="bulkDeleting" @click="showBulkDeleteDialog = true">
          {{ bulkDeleting ? 'Deleting...' : 'Delete Selected' }}
        </button>
      </div>
      <table class="admin-table">
        <thead>
          <tr>
            <th>Name</th>
            <th class="th-checkbox">
              <input type="checkbox" :checked="faculty.length > 0 && selectedIds.size === faculty.length" @change="selectAll" />
            </th>
            <th>Code</th>
            <th>Department</th>
            <th>Rank</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="member in faculty" :key="member.faculty_id" :class="{ 'row-selected': selectedIds.has(member.faculty_id) }">
            <td class="td-checkbox">
              <input type="checkbox" :checked="selectedIds.has(member.faculty_id)" @change="toggleSelect(member.faculty_id)" />
            </td>
            <td class="cell-primary cursor-pointer hover:underline" @click="viewDetails(member.faculty_id)">{{
              member.user?.username || 'Unknown' }}</td>
            <td class="cell-primary cursor-pointer hover:underline" @click="viewDetails(member.faculty_id)">{{
              member.employee_number }}</td>
            <td>{{ departmentNameById(member.department_id) }}</td>
            <td>{{ member.faculty_rank }}</td>
            <td>{{ member.employment_status }}</td>
            <td>
              <button class="admin-action-btn admin-action-edit font-medium"
                @click="viewDetails(member.faculty_id)">Details</button>
              <button class="admin-action-btn admin-action-edit" @click="openEdit(member)">Edit</button>
              <button class="admin-action-btn admin-action-delete"
                @click="confirmDeleteFaculty(member.faculty_id, member.user?.username || 'this faculty member')">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <Pagination :current-page="currentPage" :total-items="total" :page-size="pageSize" @page-change="goToPage" />
    </div>

    <div v-if="showModal" class="admin-modal-overlay">
      <div class="admin-modal admin-modal-lg">
        <h2>{{ editingFacultyId ? 'Edit Faculty' : 'Create Faculty' }}</h2>
        <form class="admin-form-grid" @submit.prevent="saveFaculty">
          <div><label class="form-label">Employee Number</label><input v-model="form.employee_number" required /></div>
          <div>
            <label class="form-label">User</label>
            <select v-model="form.user_id" :disabled="Boolean(editingFacultyId)" required>
              <option value="" disabled>Select user</option>
              <option v-for="user in users" :key="user.user_id" :value="String(user.user_id)">{{
                userLabelById(user.user_id) }}</option>
            </select>
          </div>
          <div>
            <label class="form-label">Department</label>
            <select v-model="form.department_id" required>
              <option value="" disabled>Select department</option>
              <option v-for="department in departments" :key="department.department_id"
                :value="String(department.department_id)">{{ department.department_code }} - {{
                  department.department_name }}</option>
            </select>
          </div>
          <div><label class="form-label">Hire Date</label><input v-model="form.hire_date" type="date" required /></div>
          <div><label class="form-label">Termination Date</label><input v-model="form.termination_date" type="date" />
          </div>
          <div>
            <label class="form-label">Faculty Rank</label>
            <select v-model="form.faculty_rank">
              <option value="Instructor">Instructor</option>
              <option value="Lecturer">Lecturer</option>
              <option value="Assistant Professor">Assistant Professor</option>
              <option value="Associate Professor">Associate Professor</option>
              <option value="Professor">Professor</option>
            </select>
          </div>
          <div>
            <label class="form-label">Tenure Status</label>
            <select v-model="form.tenure_status">
              <option value="non-tenure-track">Non-Tenure Track</option>
              <option value="tenure-track">Tenure Track</option>
              <option value="tenured">Tenured</option>
            </select>
          </div>
          <div>
            <label class="form-label">Employment Type</label>
            <select v-model="form.employment_type">
              <option value="full-time">Full-Time</option>
              <option value="part-time">Part-Time</option>
              <option value="adjunct">Adjunct</option>
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
          <div class="col-span-full"><label class="form-label">Office Hours</label><input v-model="form.office_hours" />
          </div>
          <div class="col-span-full"><label class="form-label">Research Interests</label><textarea
              v-model="form.research_interests" rows="3" /></div>
          <div class="admin-form-actions">
            <button type="button" class="admin-btn-cancel" @click="closeModal">Cancel</button>
            <button :disabled="saving" type="submit" class="admin-btn-save">{{ saving ? 'Saving...' : 'Save' }}</button>
          </div>
        </form>
      </div>
    </div>

    <ConfirmDeleteDialog
      :show="showDeleteDialog"
      title="Delete Faculty"
      :item-name="deleteFacultyName"
      :deleting="deleting"
      @confirm="executeDeleteFaculty"
      @cancel="showDeleteDialog = false"
    />

    <div v-if="showBulkDeleteDialog" class="admin-modal-overlay" @click.self="showBulkDeleteDialog = false">
      <div class="admin-modal admin-modal-sm">
        <h2>Delete {{ selectedIds.size }} Faculty Member(s)</h2>
        <p class="text-ink-muted mb-4">Are you sure you want to delete {{ selectedIds.size }} selected faculty member(s)? This action cannot be undone. All associated data will also be permanently deleted.</p>
        <div class="admin-form-actions">
          <button type="button" class="admin-btn-cancel" @click="showBulkDeleteDialog = false">Cancel</button>
          <button :disabled="bulkDeleting" class="admin-btn-delete-selected" @click="deleteSelectedFaculty">
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
