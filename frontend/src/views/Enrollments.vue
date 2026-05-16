<script setup>
import { onMounted, ref } from 'vue'
import { createEnrollment, deleteEnrollment, getEnrollments, getSections, getStudents, updateEnrollment } from '../services/api'
import { getApiError, pick, toNullableString } from '../components/utils/crud'
import { useToast } from '../composables/useToast'
import Pagination from '../components/Pagination.vue'
import SearchFilter from '../components/SearchFilter.vue'
import ConfirmDeleteDialog from '../components/ConfirmDeleteDialog.vue'

const toast = useToast()

const enrollments = ref([])
const students = ref([])
const sections = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingEnrollmentId = ref(null)
const currentPage = ref(1)
const pageSize = 100
const searchQuery = ref('')

const selectedIds = ref(new Set())
const selectAll = () => {
  if (selectedIds.value.size === enrollments.value.length) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(enrollments.value.map(e => e.enrollment_id))
  }
}
const toggleSelect = (id) => {
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id); else next.add(id)
  selectedIds.value = next
}

const showDeleteDialog = ref(false)
const deletingEnrollmentId = ref(null)
const deleteEnrollmentName = ref('')
const deleting = ref(false)

const defaultForm = () => ({
  student_id: '', section_id: '', enrollment_status: 'enrolled',
  grade: '', grade_points: '', credits_earned: '', attendance_percentage: '',
  midterm_grade: '', final_grade: '', is_audit: false, withdrawal_reason: '',
})

const form = ref(defaultForm())

const loadEnrollments = async () => {
  loading.value = true; error.value = ''
  try {
    const skip = (currentPage.value - 1) * pageSize
    const [enrollmentsRes, studentsRes, sectionsRes] = await Promise.all([
      getEnrollments(skip, pageSize, null, null, null, searchQuery.value), getStudents(0, 200), getSections(0, 200),
    ])
    enrollments.value = enrollmentsRes.data.enrollments
    total.value = enrollmentsRes.data.total
    students.value = studentsRes.data.students
    sections.value = sectionsRes.data.sections
  } catch (err) { error.value = getApiError(err, 'Failed to load enrollments') }
  finally { loading.value = false }
}

const goToPage = (page) => {
  selectedIds.value = new Set()
  currentPage.value = page
  loadEnrollments()
}

const onSearch = (val) => {
  selectedIds.value = new Set()
  searchQuery.value = val
  currentPage.value = 1
  loadEnrollments()
}

const openCreate = () => { editingEnrollmentId.value = null; form.value = defaultForm(); showModal.value = true }

const openEdit = (enrollment) => {
  editingEnrollmentId.value = enrollment.enrollment_id
  form.value = {
    student_id: String(enrollment.student_id || ''),
    section_id: String(enrollment.section_id || ''),
    enrollment_status: enrollment.enrollment_status || 'enrolled',
    grade: enrollment.grade || '', grade_points: enrollment.grade_points ?? '',
    credits_earned: enrollment.credits_earned ?? '',
    attendance_percentage: enrollment.attendance_percentage ?? '',
    midterm_grade: enrollment.midterm_grade || '', final_grade: enrollment.final_grade || '',
    is_audit: enrollment.is_audit ?? false, withdrawal_reason: enrollment.withdrawal_reason || '',
  }
  showModal.value = true
}

const closeModal = () => { showModal.value = false; editingEnrollmentId.value = null }

const buildCreatePayload = () => ({
  ...pick(form.value, ['enrollment_status', 'is_audit']),
  student_id: String(form.value.student_id), section_id: Number(form.value.section_id),
})

const buildUpdatePayload = () => ({
  ...pick(form.value, ['enrollment_status', 'is_audit']),
  grade: toNullableString(form.value.grade),
  grade_points: form.value.grade_points === '' ? null : Number(form.value.grade_points),
  credits_earned: form.value.credits_earned === '' ? null : Number(form.value.credits_earned),
  attendance_percentage: form.value.attendance_percentage === '' ? null : Number(form.value.attendance_percentage),
  midterm_grade: toNullableString(form.value.midterm_grade),
  final_grade: toNullableString(form.value.final_grade),
  withdrawal_reason: toNullableString(form.value.withdrawal_reason),
})

const saveEnrollment = async () => {
  saving.value = true; error.value = ''
  try {
    if (editingEnrollmentId.value) { await updateEnrollment(editingEnrollmentId.value, buildUpdatePayload()) }
    else { await createEnrollment(buildCreatePayload()) }
    closeModal(); currentPage.value = 1; await loadEnrollments()
  } catch (err) { error.value = getApiError(err, 'Failed to save enrollment') }
  finally { saving.value = false }
}

const confirmDeleteEnrollment = (enrollmentId, label) => {
  deletingEnrollmentId.value = enrollmentId
  deleteEnrollmentName.value = label
  showDeleteDialog.value = true
}

const executeDeleteEnrollment = async () => {
  deleting.value = true
  try {
    await deleteEnrollment(deletingEnrollmentId.value)
    showDeleteDialog.value = false
    currentPage.value = 1
    await loadEnrollments()
    toast.success('Enrollment deleted successfully')
  } catch (err) {
    toast.error(getApiError(err, 'Failed to delete enrollment'))
    showDeleteDialog.value = false
  } finally {
    deleting.value = false
  }
}

const bulkDeleting = ref(false)
const showBulkDeleteDialog = ref(false)
const deleteSelectedEnrollments = async () => {
  bulkDeleting.value = true
  showBulkDeleteDialog.value = false
  const ids = [...selectedIds.value]
  let successCount = 0
  let failCount = 0
  for (const id of ids) {
    try {
      await deleteEnrollment(id)
      successCount++
    } catch {
      failCount++
    }
  }
  selectedIds.value = new Set()
  currentPage.value = 1
  await loadEnrollments()
  if (failCount > 0) {
    toast.warning(`Deleted ${successCount} enrollment(s), ${failCount} failed`)
  } else {
    toast.success(`Deleted ${successCount} enrollment(s)`)
  }
  bulkDeleting.value = false
}

const studentLabelById = (studentId) => {
  const match = students.value.find((student) => student.student_id === studentId)
  return match ? match.student_number : studentId
}

const sectionLabelById = (sectionId) => {
  const match = sections.value.find((section) => section.section_id === sectionId)
  return match ? match.section_number : `ID ${sectionId}`
}

onMounted(loadEnrollments)
</script>

<template>
  <div>
    <div class="admin-page-header">
      <h1>Enrollments</h1>
      <button class="admin-btn-add" @click="openCreate">+ Add Enrollment</button>
    </div>

    <div v-if="error" class="admin-error">{{ error }}</div>
    <div v-if="loading" class="admin-loading">Loading enrollments...</div>

    <div v-else class="admin-table-card">
      <div class="px-4 pt-3 pb-2 border-b border-border-light">
        <SearchFilter v-model="searchQuery" @search="onSearch" placeholder="Search enrollments..." />
      </div>
      <div class="admin-record-count">{{ total }} enrollment(s)</div>
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
              <input type="checkbox" :checked="enrollments.length > 0 && selectedIds.size === enrollments.length" @change="selectAll" />
            </th>
            <th>ID</th>
            <th>Student</th>
            <th>Section</th>
            <th>Status</th>
            <th>Grade</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="enrollment in enrollments" :key="enrollment.enrollment_id" :class="{ 'row-selected': selectedIds.has(enrollment.enrollment_id) }">
            <td class="td-checkbox">
              <input type="checkbox" :checked="selectedIds.has(enrollment.enrollment_id)" @change="toggleSelect(enrollment.enrollment_id)" />
            </td>
            <td class="cell-primary">{{ enrollment.enrollment_id }}</td>
            <td>{{ studentLabelById(enrollment.student_id) }}</td>
            <td>{{ sectionLabelById(enrollment.section_id) }}</td>
            <td>{{ enrollment.enrollment_status }}</td>
            <td>{{ enrollment.grade || '-' }}</td>
            <td>
              <button class="admin-action-btn admin-action-edit" @click="openEdit(enrollment)">Edit</button>
              <button class="admin-action-btn admin-action-delete"
                @click="confirmDeleteEnrollment(enrollment.enrollment_id, 'Enrollment #' + enrollment.enrollment_id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <Pagination :current-page="currentPage" :total-items="total" :page-size="pageSize" @page-change="goToPage" />
    </div>

    <div v-if="showModal" class="admin-modal-overlay">
      <div class="admin-modal admin-modal-lg">
        <h2>{{ editingEnrollmentId ? 'Edit Enrollment' : 'Create Enrollment' }}</h2>
        <form class="admin-form-grid" @submit.prevent="saveEnrollment">
          <div>
            <label class="form-label">Student</label>
            <select v-model="form.student_id" :disabled="Boolean(editingEnrollmentId)" required>
              <option value="" disabled>Select student</option>
              <option v-for="student in students" :key="student.student_id" :value="String(student.student_id)">{{
                student.student_number }}</option>
            </select>
          </div>
          <div>
            <label class="form-label">Section</label>
            <select v-model="form.section_id" :disabled="Boolean(editingEnrollmentId)" required>
              <option value="" disabled>Select section</option>
              <option v-for="section in sections" :key="section.section_id" :value="String(section.section_id)">{{
                section.section_number }} (Course {{ section.course_id }})</option>
            </select>
          </div>
          <div>
            <label class="form-label">Enrollment Status</label>
            <select v-model="form.enrollment_status">
              <option value="enrolled">Enrolled</option>
              <option value="dropped">Dropped</option>
              <option value="withdrawn">Withdrawn</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          <label class="admin-checkbox-row"><input v-model="form.is_audit" type="checkbox" /> Audit Course</label>
          <div>
            <label class="form-label">Grade</label>
            <select v-model="form.grade">
              <option value="">Select Grade</option>
              <option value="S1">Semester 1</option>
              <option value="S2">Semester 2</option>
            </select>
          </div>
          <div><label class="form-label">GPA</label><input v-model="form.grade_points" type="number" step="0.01" min="0"
              max="4.0" /></div>
          <div><label class="form-label">Credits Earned</label><input v-model="form.credits_earned" type="number"
              min="0" /></div>
          <div><label class="form-label">Attendance %</label><input v-model="form.attendance_percentage" type="number"
              step="0.01" min="0" max="100" /></div>
          <div>
            <label class="form-label">Midterm Grade</label>
            <select v-model="form.midterm_grade">
              <option value="">Select Grade</option>
              <option value="Y1">Year 1</option>
              <option value="Y2">Year 2</option>
              <option value="Y3">Year 3</option>
              <option value="Y4">Year 4</option>
            </select>
          </div>
          <div>
            <label class="form-label">Final Grade</label>
            <select v-model="form.final_grade">
              <option value="">Select Grade</option>
              <option value="Y1">Year 1</option>
              <option value="Y2">Year 2</option>
              <option value="Y3">Year 3</option>
              <option value="Y4">Year 4</option>
            </select>
          </div>
          <div class="col-span-full"><label class="form-label">Withdrawal Reason</label><textarea
              v-model="form.withdrawal_reason" rows="3" /></div>
          <div class="admin-form-actions">
            <button type="button" class="admin-btn-cancel" @click="closeModal">Cancel</button>
            <button :disabled="saving" type="submit" class="admin-btn-save">{{ saving ? 'Saving...' : 'Save' }}</button>
          </div>
        </form>
      </div>
    </div>

    <ConfirmDeleteDialog
      :show="showDeleteDialog"
      title="Delete Enrollment"
      :item-name="deleteEnrollmentName"
      :deleting="deleting"
      @confirm="executeDeleteEnrollment"
      @cancel="showDeleteDialog = false"
    />

    <div v-if="showBulkDeleteDialog" class="admin-modal-overlay" @click.self="showBulkDeleteDialog = false">
      <div class="admin-modal admin-modal-sm">
        <h2>Delete {{ selectedIds.size }} Enrollment(s)</h2>
        <p class="text-ink-muted mb-4">Are you sure you want to delete {{ selectedIds.size }} selected enrollment(s)? All associated data will be permanently deleted.</p>
        <div class="admin-form-actions">
          <button type="button" class="admin-btn-cancel" @click="showBulkDeleteDialog = false">Cancel</button>
          <button :disabled="bulkDeleting" class="admin-btn-delete-selected" @click="deleteSelectedEnrollments">
            {{ bulkDeleting ? 'Deleting...' : 'Delete All' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>


