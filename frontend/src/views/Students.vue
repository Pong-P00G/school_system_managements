<script setup>
import { onMounted, ref } from 'vue'
import { createStudent, deleteStudent, getPrograms, getStudentAccount, getStudentEnrollments, getStudents, getUsers, updateStudent } from '../services/api'
import { getApiError, pick, toDateInput, toNullableInt, toNullableString } from '../components/utils/crud'
import { useToast } from '../composables/useToast'
import Pagination from '../components/Pagination.vue'
import SearchFilter from '../components/SearchFilter.vue'
import ConfirmDeleteDialog from '../components/ConfirmDeleteDialog.vue'

const toast = useToast()

const students = ref([])
const programs = ref([])
const users = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingStudentId = ref(null)
const currentPage = ref(1)
const pageSize = 100
const searchQuery = ref('')

const selectedIds = ref(new Set())
const selectAll = () => {
  if (selectedIds.value.size === students.value.length) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(students.value.map(s => s.student_id))
  }
}
const toggleSelect = (id) => {
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id); else next.add(id)
  selectedIds.value = next
}

const showDeleteDialog = ref(false)
const deletingStudentId = ref(null)
const deleteStudentName = ref('')
const deleting = ref(false)

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
    const skip = (currentPage.value - 1) * pageSize
    const [studentsRes, programsRes, usersRes] = await Promise.all([
      getStudents(skip, pageSize, null, null, null, searchQuery.value), getPrograms(0, 200), getUsers(0, 200),
    ])
    students.value = studentsRes.data.students; total.value = studentsRes.data.total
    programs.value = programsRes.data.programs; users.value = usersRes.data.users
  } catch (err) { error.value = getApiError(err, 'Failed to load students') }
  finally { loading.value = false }
}

const goToPage = (page) => {
  selectedIds.value = new Set()
  currentPage.value = page
  loadStudents()
}

const onSearch = (val) => {
  selectedIds.value = new Set()
  searchQuery.value = val
  currentPage.value = 1
  loadStudents()
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
    closeModal(); currentPage.value = 1; await loadStudents()
  } catch (err) { error.value = getApiError(err, 'Failed to save student') }
  finally { saving.value = false }
}

const confirmDeleteStudent = (studentId, studentNumber) => {
  deletingStudentId.value = studentId
  deleteStudentName.value = `Student #${studentNumber}`
  showDeleteDialog.value = true
}

const executeDeleteStudent = async () => {
  deleting.value = true
  try {
    await deleteStudent(deletingStudentId.value)
    showDeleteDialog.value = false
    currentPage.value = 1
    await loadStudents()
    toast.success('Student deleted successfully')
  } catch (err) {
    toast.error(getApiError(err, 'Failed to delete student'))
    showDeleteDialog.value = false
  } finally {
    deleting.value = false
  }
}


const bulkDeleting = ref(false)
const showBulkDeleteDialog = ref(false)
const deleteSelectedStudents = async () => {
  bulkDeleting.value = true
  showBulkDeleteDialog.value = false
  const ids = [...selectedIds.value]
  let successCount = 0
  let failCount = 0
  for (const id of ids) {
    try {
      await deleteStudent(id)
      successCount++
    } catch {
      failCount++
    }
  }
  selectedIds.value = new Set()
  currentPage.value = 1
  await loadStudents()
  if (failCount > 0) {
    toast.warning(`Deleted ${successCount} student(s), ${failCount} failed`)
  } else {
    toast.success(`Deleted ${successCount} student(s)`)
  }
  bulkDeleting.value = false
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
      <div class="px-4 pt-3 pb-2 border-b border-border-light">
        <SearchFilter v-model="searchQuery" @search="onSearch" placeholder="Search students..." />
      </div>
      <div class="admin-record-count">{{ total }} student(s)</div>
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
              <input type="checkbox" :checked="students.length > 0 && selectedIds.size === students.length" @change="selectAll" />
            </th>
            <th>Student #</th>
            <th>Program</th>
            <th>Standing</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="student in students" :key="student.student_id" :class="{ 'row-selected': selectedIds.has(student.student_id) }">
            <td class="td-checkbox">
              <input type="checkbox" :checked="selectedIds.has(student.student_id)" @change="toggleSelect(student.student_id)" />
            </td>
            <td class="cell-primary">{{ student.student_number }}</td>
            <td>{{ programNameById(student.program_id) }}</td>
            <td>{{ student.academic_standing }}</td>
            <td>{{ student.enrollment_status }}</td>
            <td>
              <button class="admin-action-btn admin-action-edit" @click="openEdit(student)">Edit</button>
              <button class="admin-action-btn admin-action-delete"
                @click="confirmDeleteStudent(student.student_id, student.student_number)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <Pagination :current-page="currentPage" :total-items="total" :page-size="pageSize" @page-change="goToPage" />
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

    <ConfirmDeleteDialog
      :show="showDeleteDialog"
      title="Delete Student"
      :item-name="deleteStudentName"
      :deleting="deleting"
      @confirm="executeDeleteStudent"
      @cancel="showDeleteDialog = false"
    />

    <div v-if="showBulkDeleteDialog" class="admin-modal-overlay" @click.self="showBulkDeleteDialog = false">
      <div class="admin-modal admin-modal-sm">
        <h2>Delete {{ selectedIds.size }} Student(s)</h2>
        <p class="text-ink-muted mb-4">Are you sure you want to delete {{ selectedIds.size }} selected student(s)? This action cannot be undone. All associated data will also be permanently deleted.</p>
        <div class="admin-form-actions">
          <button type="button" class="admin-btn-cancel" @click="showBulkDeleteDialog = false">Cancel</button>
          <button :disabled="bulkDeleting" class="admin-btn-delete-selected" @click="deleteSelectedStudents">
            {{ bulkDeleting ? 'Deleting...' : 'Delete All' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>


