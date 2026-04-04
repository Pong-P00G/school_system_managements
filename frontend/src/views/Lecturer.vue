<script setup>
import { onMounted, ref } from 'vue'
import { createFaculty, deleteFaculty, getDepartments, getFaculty, getUsers, updateFaculty } from '../services/api'
import { getApiError, pick, toDateInput, toNullableInt, toNullableString } from '../components/utils/crud'

const faculty = ref([])
const departments = ref([])
const users = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingFacultyId = ref(null)

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
    const [facultyRes, departmentsRes, usersRes] = await Promise.all([
      getFaculty(0, 200), getDepartments(0, 200), getUsers(0, 200),
    ])
    faculty.value = facultyRes.data.faculty; total.value = facultyRes.data.total
    departments.value = departmentsRes.data.departments; users.value = usersRes.data.users
  } catch (err) { error.value = getApiError(err, 'Failed to load faculty') }
  finally { loading.value = false }
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
    closeModal(); await loadFaculty()
  } catch (err) { error.value = getApiError(err, 'Failed to save faculty') }
  finally { saving.value = false }
}

const removeFaculty = async (facultyId) => {
  if (!confirm('Delete this faculty profile?')) return
  error.value = ''
  try { await deleteFaculty(facultyId); await loadFaculty() }
  catch (err) { error.value = getApiError(err, 'Failed to delete faculty') }
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
      <div class="admin-record-count">{{ total }} faculty member(s)</div>
      <table class="admin-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Code</th>
            <th>Department</th>
            <th>Rank</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="member in faculty" :key="member.faculty_id">
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
                @click="removeFaculty(member.faculty_id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
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
  </div>
</template>
