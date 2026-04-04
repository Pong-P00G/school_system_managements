<script setup>
import { onMounted, ref } from 'vue'
import { createCourse, deleteCourse, getCourses, getDepartments, updateCourse } from '../services/api'
import { getApiError, pick, toNullableString } from '../components/utils/crud'

const courses = ref([])
const departments = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingCourseId = ref(null)

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
    const [coursesRes, departmentsRes] = await Promise.all([getCourses(0, 200), getDepartments(0, 200)])
    courses.value = coursesRes.data.courses
    total.value = coursesRes.data.total
    departments.value = departmentsRes.data.departments
  } catch (err) {
    error.value = getApiError(err, 'Failed to load courses')
  } finally {
    loading.value = false
  }
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
    await loadCourses()
  } catch (err) {
    error.value = getApiError(err, 'Failed to save course')
  } finally {
    saving.value = false
  }
}

const removeCourse = async (courseId) => {
  if (!confirm('Delete this course?')) return
  error.value = ''
  try {
    await deleteCourse(courseId)
    await loadCourses()
  } catch (err) {
    error.value = getApiError(err, 'Failed to delete course')
  }
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
      <div class="admin-record-count">{{ total }} course(s)</div>
      <table class="admin-table">
        <thead>
          <tr>
            <th>Code</th>
            <th>Name</th>
            <th>Department</th>
            <th>Credits</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="course in courses" :key="course.course_id">
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
                @click="removeCourse(course.course_id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
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
  </div>
</template>
