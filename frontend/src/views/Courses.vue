<script setup>
import { onMounted, ref } from 'vue'
import { createCourse, deleteCourse, getCourses, getDepartments, updateCourse } from '../services/api'
import { getApiError, pick, toNullableString } from '../components/utils/crud'
import { useToast } from '../composables/useToast'
import Pagination from '../components/Pagination.vue'
import SearchFilter from '../components/SearchFilter.vue'
import ConfirmDeleteDialog from '../components/ConfirmDeleteDialog.vue'

const toast = useToast()

const courses = ref([])
const departments = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingCourseId = ref(null)
const currentPage = ref(1)
const pageSize = 100
const searchQuery = ref('')

const selectedIds = ref(new Set())
const selectAll = () => {
  if (selectedIds.value.size === courses.value.length) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(courses.value.map(c => c.course_id))
  }
}
const toggleSelect = (id) => {
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id); else next.add(id)
  selectedIds.value = next
}

const showDeleteDialog = ref(false)
const deletingCourseId = ref(null)
const deleteCourseName = ref('')
const deleting = ref(false)

const defaultForm = () => ({
  course_code: '',
  course_name: '',
  department_id: '',
  credits: 3,
  course_level: '',
  lecture_hours: 0,
  lab_hours: 0,
  description: '',
  learning_outcomes: '',
  syllabus_url: '',
  is_active: true,
})

const form = ref(defaultForm())

const loadCourses = async () => {
  loading.value = true
  error.value = ''
  try {
    const skip = (currentPage.value - 1) * pageSize
    const [coursesRes, departmentsRes] = await Promise.all([getCourses(skip, pageSize, null, searchQuery.value), getDepartments(0, 200)])
    courses.value = coursesRes.data.courses
    total.value = coursesRes.data.total
    departments.value = departmentsRes.data.departments
  } catch (err) {
    error.value = getApiError(err, 'Failed to load courses')
  } finally {
    loading.value = false
  }
}

const goToPage = (page) => {
  selectedIds.value = new Set()
  currentPage.value = page
  loadCourses()
}

const onSearch = (val) => {
  selectedIds.value = new Set()
  searchQuery.value = val
  currentPage.value = 1
  loadCourses()
}

const openCreate = () => {
  editingCourseId.value = null
  form.value = defaultForm()
  showModal.value = true
}

const openEdit = (course) => {
  editingCourseId.value = course.course_id
  form.value = {
    course_code: course.course_code || '',
    course_name: course.course_name || '',
    department_id: String(course.department_id || ''),
    credits: Number(course.credits || 3),
    course_level: course.course_level || '',
    lecture_hours: Number(course.lecture_hours || 0),
    lab_hours: Number(course.lab_hours || 0),
    description: course.description || '',
    learning_outcomes: course.learning_outcomes || '',
    syllabus_url: course.syllabus_url || '',
    is_active: course.is_active ?? true,
  }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingCourseId.value = null
}

const buildPayload = () => ({
  ...pick(form.value, ['course_code', 'course_name', 'is_active']),
  department_id: Number(form.value.department_id),
  credits: Number(form.value.credits),
  course_level: toNullableString(form.value.course_level),
  lecture_hours: Number(form.value.lecture_hours || 0),
  lab_hours: Number(form.value.lab_hours || 0),
  description: toNullableString(form.value.description),
  learning_outcomes: toNullableString(form.value.learning_outcomes),
  syllabus_url: toNullableString(form.value.syllabus_url),
})

const saveCourse = async () => {
  saving.value = true
  error.value = ''
  try {
    const payload = buildPayload()
    if (editingCourseId.value) {
      await updateCourse(editingCourseId.value, payload)
    } else {
      await createCourse(payload)
    }
    closeModal()
    currentPage.value = 1
    await loadCourses()
  } catch (err) {
    error.value = getApiError(err, 'Failed to save course')
  } finally {
    saving.value = false
  }
}

const confirmDeleteCourse = (courseId, courseName) => {
  deletingCourseId.value = courseId
  deleteCourseName.value = courseName
  showDeleteDialog.value = true
}

const executeDeleteCourse = async () => {
  deleting.value = true
  try {
    await deleteCourse(deletingCourseId.value)
    showDeleteDialog.value = false
    currentPage.value = 1
    await loadCourses()
    toast.success('Course deleted successfully')
  } catch (err) {
    toast.error(getApiError(err, 'Failed to delete course'))
    showDeleteDialog.value = false
  } finally {
    deleting.value = false
  }
}

const bulkDeleting = ref(false)
const showBulkDeleteDialog = ref(false)
const deleteSelectedCourses = async () => {
  bulkDeleting.value = true
  showBulkDeleteDialog.value = false
  const ids = [...selectedIds.value]
  let successCount = 0
  let failCount = 0
  for (const id of ids) {
    try {
      await deleteCourse(id)
      successCount++
    } catch {
      failCount++
    }
  }
  selectedIds.value = new Set()
  currentPage.value = 1
  await loadCourses()
  if (failCount > 0) {
    toast.warning(`Deleted ${successCount} course(s), ${failCount} failed`)
  } else {
    toast.success(`Deleted ${successCount} course(s)`)
  }
  bulkDeleting.value = false
}

const departmentNameById = (departmentId) => {
  const match = departments.value.find((department) => department.department_id === departmentId)
  return match ? match.department_name : `ID ${departmentId}`
}

onMounted(loadCourses)
</script>

<template>
  <div>
    <div class="admin-page-header">
      <h1>Courses</h1>
      <button class="admin-btn-add" @click="openCreate">+ Add Course</button>
    </div>

    <div v-if="error" class="admin-error">{{ error }}</div>
    <div v-if="loading" class="admin-loading">Loading courses...</div>

    <div v-else class="admin-table-card">
      <div class="px-4 pt-3 pb-2 border-b border-border-light">
        <SearchFilter v-model="searchQuery" @search="onSearch" placeholder="Search courses..." />
      </div>
      <div class="admin-record-count">{{ total }} course(s)</div>
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
              <input type="checkbox" :checked="courses.length > 0 && selectedIds.size === courses.length" @change="selectAll" />
            </th>
            <th>Code</th>
            <th>Name</th>
            <th>Department</th>
            <th>Credits</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="course in courses" :key="course.course_id" :class="{ 'row-selected': selectedIds.has(course.course_id) }">
            <td class="td-checkbox">
              <input type="checkbox" :checked="selectedIds.has(course.course_id)" @change="toggleSelect(course.course_id)" />
            </td>
            <td class="cell-primary">{{ course.course_code }}</td>
            <td class="font-medium text-ink">{{ course.course_name }}</td>
            <td>{{ departmentNameById(course.department_id) }}</td>
            <td>{{ course.credits }}</td>
            <td>
              <span class="admin-badge" :class="course.is_active ? 'admin-badge-active' : 'admin-badge-inactive'">
                {{ course.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td>
              <button class="admin-action-btn admin-action-edit" @click="openEdit(course)">Edit</button>
              <button class="admin-action-btn admin-action-delete"
                @click="confirmDeleteCourse(course.course_id, course.course_name)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <Pagination :current-page="currentPage" :total-items="total" :page-size="pageSize" @page-change="goToPage" />
    </div>

    <div v-if="showModal" class="admin-modal-overlay">
      <div class="admin-modal admin-modal-lg">
        <h2>{{ editingCourseId ? 'Edit Course' : 'Create Course' }}</h2>
        <form class="admin-form-grid" @submit.prevent="saveCourse">
          <div>
            <label class="form-label">Course Code</label>
            <input v-model="form.course_code" required />
          </div>
          <div>
            <label class="form-label">Course Name</label>
            <input v-model="form.course_name" required />
          </div>
          <div>
            <label class="form-label">Department</label>
            <select v-model="form.department_id" required>
              <option value="" disabled>Select department</option>
              <option v-for="department in departments" :key="department.department_id"
                :value="String(department.department_id)">
                {{ department.department_code }} - {{ department.department_name }}
              </option>
            </select>
          </div>
          <div>
            <label class="form-label">Credits</label>
            <input v-model.number="form.credits" type="number" min="1" max="12" required />
          </div>
          <div>
            <label class="form-label">Course Level</label>
            <input v-model="form.course_level" placeholder="undergraduate" />
          </div>
          <div>
            <label class="form-label">Syllabus URL</label>
            <input v-model="form.syllabus_url" />
          </div>
          <div>
            <label class="form-label">Lecture Hours</label>
            <input v-model.number="form.lecture_hours" type="number" step="0.25" min="0" />
          </div>
          <div>
            <label class="form-label">Lab Hours</label>
            <input v-model.number="form.lab_hours" type="number" step="0.25" min="0" />
          </div>
          <div class="col-span-full">
            <label class="form-label">Description</label>
            <textarea v-model="form.description" rows="3" />
          </div>
          <div class="col-span-full">
            <label class="form-label">Learning Outcomes</label>
            <textarea v-model="form.learning_outcomes" rows="3" />
          </div>
          <label class="admin-checkbox-row">
            <input v-model="form.is_active" type="checkbox" />
            Active
          </label>
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
      title="Delete Course"
      :item-name="deleteCourseName"
      :deleting="deleting"
      @confirm="executeDeleteCourse"
      @cancel="showDeleteDialog = false"
    />

    <div v-if="showBulkDeleteDialog" class="admin-modal-overlay" @click.self="showBulkDeleteDialog = false">
      <div class="admin-modal admin-modal-sm">
        <h2>Delete {{ selectedIds.size }} Course(s)</h2>
        <p class="text-ink-muted mb-4">Are you sure you want to delete {{ selectedIds.size }} selected course(s)? All associated data will be permanently deleted.</p>
        <div class="admin-form-actions">
          <button type="button" class="admin-btn-cancel" @click="showBulkDeleteDialog = false">Cancel</button>
          <button :disabled="bulkDeleting" class="admin-btn-delete-selected" @click="deleteSelectedCourses">
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
