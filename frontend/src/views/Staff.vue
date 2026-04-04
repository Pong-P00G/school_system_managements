<script setup>
import { onMounted, ref } from 'vue'
import { createStaff, deleteStaff, getDepartments, getStaff, getUsers, updateStaff } from '../services/api'
import { getApiError, pick, toDateInput, toNullableInt, toNullableString } from '../components/utils/crud'

const staff = ref([])
const departments = ref([])
const users = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingStaffId = ref(null)

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
    const [staffRes, departmentsRes, usersRes] = await Promise.all([
      getStaff(0, 200), getDepartments(0, 200), getUsers(0, 200),
    ])
    staff.value = staffRes.data.staff; total.value = staffRes.data.total
    departments.value = departmentsRes.data.departments; users.value = usersRes.data.users
  } catch (err) { error.value = getApiError(err, 'Failed to load staff') }
  finally { loading.value = false }
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
    closeModal(); await loadStaff()
  } catch (err) { error.value = getApiError(err, 'Failed to save staff member') }
  finally { saving.value = false }
}

const removeStaff = async (staffId) => {
  if (!confirm('Delete this staff profile?')) return
  error.value = ''
  try { await deleteStaff(staffId); await loadStaff() }
  catch (err) { error.value = getApiError(err, 'Failed to delete staff member') }
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
      <div class="admin-record-count">{{ total }} staff member(s)</div>
      <table class="admin-table">
        <thead>
          <tr>
            <th>Employee</th>
            <th>Job Title</th>
            <th>Department</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="member in staff" :key="member.staff_id">
            <td class="cell-primary">{{ member.employee_number }}</td>
            <td>{{ member.job_title }}</td>
            <td>{{ departmentNameById(member.department_id) }}</td>
            <td>{{ member.employment_status }}</td>
            <td>
              <button class="admin-action-btn admin-action-edit" @click="openEdit(member)">Edit</button>
              <button class="admin-action-btn admin-action-delete" @click="removeStaff(member.staff_id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
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
  </div>
</template>
