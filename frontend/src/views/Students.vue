<script setup>
import { onMounted, ref } from 'vue'
import { createStudent, deleteStudent, getPrograms, getStudents, getUsers, updateStudent } from '../services/api'
import { getApiError, pick, toDateInput, toNullableInt, toNullableString } from '../components/utils/crud'

const students = ref([])
const programs = ref([])
const users = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingStudentId = ref(null)

const defaultForm = () => ({
  student_number: '', user_id: '', program_id: '',
  enrollment_date: new Date().toISOString().slice(0, 10), expected_graduation_date: '',
  current_term_id: '', academic_standing: 'good_standing', enrollment_status: 'active',
  advisor_id: '', admission_type: '', is_international: false, visa_type: '',
})

const form = ref(defaultForm())

const loadStudents = async () => {
  loading.value = true; error.value = ''
  try {
    const [studentsRes, programsRes, usersRes] = await Promise.all([
      getStudents(0, 200), getPrograms(0, 200), getUsers(0, 200),
    ])
    students.value = studentsRes.data.students; total.value = studentsRes.data.total
    programs.value = programsRes.data.programs; users.value = usersRes.data.users
  } catch (err) { error.value = getApiError(err, 'Failed to load students') }
  finally { loading.value = false }
}

const openCreate = () => { editingStudentId.value = null; form.value = defaultForm(); showModal.value = true }

const openEdit = (student) => {
  editingStudentId.value = student.student_id
  form.value = {
    student_number: student.student_number || '',
    user_id: String(student.student_id || ''), program_id: String(student.program_id || ''),
    enrollment_date: toDateInput(student.enrollment_date),
    expected_graduation_date: toDateInput(student.expected_graduation_date),
    current_term_id: student.current_term_id ?? '',
    academic_standing: student.academic_standing || 'good_standing',
    enrollment_status: student.enrollment_status || 'active',
    advisor_id: student.advisor_id || '', admission_type: student.admission_type || '',
    is_international: student.is_international ?? false, visa_type: student.visa_type || '',
  }
  showModal.value = true
}

const closeModal = () => { showModal.value = false; editingStudentId.value = null }

const buildCreatePayload = () => ({
  ...pick(form.value, ['student_number', 'academic_standing', 'enrollment_status', 'is_international']),
  user_id: String(form.value.user_id), program_id: Number(form.value.program_id),
  enrollment_date: form.value.enrollment_date,
  expected_graduation_date: toNullableString(form.value.expected_graduation_date),
  current_term_id: toNullableInt(form.value.current_term_id),
  advisor_id: toNullableString(form.value.advisor_id), admission_type: toNullableString(form.value.admission_type),
  visa_type: toNullableString(form.value.visa_type),
})

const buildUpdatePayload = () => ({
  ...pick(form.value, ['student_number', 'academic_standing', 'enrollment_status', 'is_international']),
  program_id: Number(form.value.program_id), enrollment_date: form.value.enrollment_date,
  expected_graduation_date: toNullableString(form.value.expected_graduation_date),
  current_term_id: toNullableInt(form.value.current_term_id),
  advisor_id: toNullableString(form.value.advisor_id), admission_type: toNullableString(form.value.admission_type),
  visa_type: toNullableString(form.value.visa_type),
})

const saveStudent = async () => {
  saving.value = true; error.value = ''
  try {
    if (editingStudentId.value) { await updateStudent(editingStudentId.value, buildUpdatePayload()) }
    else { await createStudent(buildCreatePayload()) }
    closeModal(); await loadStudents()
  } catch (err) { error.value = getApiError(err, 'Failed to save student') }
  finally { saving.value = false }
}

const removeStudent = async (studentId) => {
  if (!confirm('Delete this student profile?')) return
  error.value = ''
  try { await deleteStudent(studentId); await loadStudents() }
  catch (err) { error.value = getApiError(err, 'Failed to delete student') }
}

const programNameById = (programId) => {
  const match = programs.value.find((program) => program.program_id === programId)
  return match ? match.program_name : `ID ${programId}`
}

const userLabelById = (userId) => {
  const match = users.value.find((user) => user.user_id === userId)
  if (!match) return userId
  return `${match.username} (${match.email})`
}

onMounted(loadStudents)
</script>

<template>
  <div>
    <div class="admin-page-header">
      <h1>Students</h1>
      <button class="admin-btn-add" @click="openCreate">+ Add Student</button>
    </div>

    <div v-if="error" class="admin-error">{{ error }}</div>
    <div v-if="loading" class="admin-loading">Loading students...</div>

    <div v-else class="admin-table-card">
      <div class="admin-record-count">{{ total }} student(s)</div>
      <table class="admin-table">
        <thead>
          <tr>
            <th>Student #</th>
            <th>Program</th>
            <th>Standing</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="student in students" :key="student.student_id">
            <td class="cell-primary">{{ student.student_number }}</td>
            <td>{{ programNameById(student.program_id) }}</td>
            <td>{{ student.academic_standing }}</td>
            <td>{{ student.enrollment_status }}</td>
            <td>
              <button class="admin-action-btn admin-action-edit" @click="openEdit(student)">Edit</button>
              <button class="admin-action-btn admin-action-delete"
                @click="removeStudent(student.student_id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showModal" class="admin-modal-overlay">
      <div class="admin-modal admin-modal-lg">
        <h2>{{ editingStudentId ? 'Edit Student' : 'Create Student' }}</h2>
        <form class="admin-form-grid" @submit.prevent="saveStudent">
          <div><label class="form-label">Student Number</label><input v-model="form.student_number" required /></div>
          <div>
            <label class="form-label">User</label>
            <select v-model="form.user_id" :disabled="Boolean(editingStudentId)" required>
              <option value="" disabled>Select user</option>
              <option v-for="user in users" :key="user.user_id" :value="String(user.user_id)">{{
                userLabelById(user.user_id) }}</option>
            </select>
          </div>
          <div>
            <label class="form-label">Program</label>
            <select v-model="form.program_id" required>
              <option value="" disabled>Select program</option>
              <option v-for="program in programs" :key="program.program_id" :value="String(program.program_id)">{{
                program.program_code }} - {{ program.program_name }}</option>
            </select>
          </div>
          <div><label class="form-label">Enrollment Date</label><input v-model="form.enrollment_date" type="date"
              required /></div>
          <div><label class="form-label">Expected Graduation</label><input v-model="form.expected_graduation_date"
              type="date" /></div>
          <div><label class="form-label">Current Term ID</label><input v-model="form.current_term_id" type="number"
              min="1" /></div>
          <div>
            <label class="form-label">Academic Standing</label>
            <select v-model="form.academic_standing">
              <option value="good_standing">Good Standing</option>
              <option value="probation">Probation</option>
              <option value="honors">Honors</option>
              <option value="deans_list">Deans List</option>
            </select>
          </div>
          <div>
            <label class="form-label">Enrollment Status</label>
            <select v-model="form.enrollment_status">
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="graduated">Graduated</option>
              <option value="withdrawn">Withdrawn</option>
            </select>
          </div>
          <div><label class="form-label">Advisor ID</label><input v-model="form.advisor_id" /></div>
          <div><label class="form-label">Admission Type</label><input v-model="form.admission_type" /></div>
          <label class="admin-checkbox-row"><input v-model="form.is_international" type="checkbox" /> International
            Student</label>
          <div><label class="form-label">Visa Type</label><input v-model="form.visa_type" /></div>
          <div class="admin-form-actions">
            <button type="button" class="admin-btn-cancel" @click="closeModal">Cancel</button>
            <button :disabled="saving" type="submit" class="admin-btn-save">{{ saving ? 'Saving...' : 'Save' }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
