<script setup>
import { onMounted, ref } from 'vue'
import { createSection, deleteSection, getCourses, getSections, getTerms, getUsers, updateSection } from '../services/api'
import { getApiError, pick, toDateInput, toNullableInt, toNullableString } from '../components/utils/crud'

const sections = ref([])
const courses = ref([])
const terms = ref([])
const users = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingSectionId = ref(null)

const defaultForm = () => ({
  course_id: '', term_id: '', section_number: '', instructor_id: '',
  max_capacity: 30, room_id: '', schedule_pattern: '',
  start_time: '', end_time: '', start_date: '', end_date: '',
  delivery_mode: 'in-person', meeting_url: '', syllabus_url: '', status: 'planned',
})

const form = ref(defaultForm())

const loadSections = async () => {
  loading.value = true; error.value = ''
  try {
    const [sectionsRes, coursesRes, termsRes, usersRes] = await Promise.all([
      getSections(0, 200), getCourses(0, 200), getTerms(0, 200), getUsers(0, 200),
    ])
    sections.value = sectionsRes.data.sections; total.value = sectionsRes.data.total
    courses.value = coursesRes.data.courses; terms.value = termsRes.data.terms; users.value = usersRes.data.users
  } catch (err) { error.value = getApiError(err, 'Failed to load sections') }
  finally { loading.value = false }
}

const openCreate = () => { editingSectionId.value = null; form.value = defaultForm(); showModal.value = true }

const openEdit = (section) => {
  editingSectionId.value = section.section_id
  form.value = {
    course_id: String(section.course_id || ''), term_id: String(section.term_id || ''),
    section_number: section.section_number || '', instructor_id: String(section.instructor_id || ''),
    max_capacity: Number(section.max_capacity || 30), room_id: section.room_id ?? '',
    schedule_pattern: section.schedule_pattern || '',
    start_time: section.start_time || '', end_time: section.end_time || '',
    start_date: toDateInput(section.start_date), end_date: toDateInput(section.end_date),
    delivery_mode: section.delivery_mode || 'in-person',
    meeting_url: section.meeting_url || '', syllabus_url: section.syllabus_url || '',
    status: section.status || 'planned',
  }
  showModal.value = true
}

const closeModal = () => { showModal.value = false; editingSectionId.value = null }

const buildPayload = () => ({
  ...pick({
    ...form.value,
    section_number: String(form.value.section_number || '').trim(),
    delivery_mode: String(form.value.delivery_mode || '').trim(),
    status: String(form.value.status || '').trim(),
  }, ['section_number', 'delivery_mode', 'status']),
  course_id: Number(form.value.course_id), term_id: Number(form.value.term_id),
  max_capacity: Number(form.value.max_capacity),
  instructor_id: toNullableString(form.value.instructor_id),
  room_id: toNullableInt(form.value.room_id),
  schedule_pattern: toNullableString(form.value.schedule_pattern),
  start_time: toNullableString(form.value.start_time), end_time: toNullableString(form.value.end_time),
  start_date: toNullableString(form.value.start_date), end_date: toNullableString(form.value.end_date),
  meeting_url: toNullableString(form.value.meeting_url), syllabus_url: toNullableString(form.value.syllabus_url),
})

const saveSection = async () => {
  saving.value = true; error.value = ''
  try {
    const payload = buildPayload()
    if (editingSectionId.value) { await updateSection(editingSectionId.value, payload) }
    else { await createSection(payload) }
    closeModal(); await loadSections()
  } catch (err) { error.value = getApiError(err, 'Failed to save section') }
  finally { saving.value = false }
}

const removeSection = async (sectionId) => {
  if (!confirm('Delete this section?')) return
  error.value = ''
  try { await deleteSection(sectionId); await loadSections() }
  catch (err) { error.value = getApiError(err, 'Failed to delete section') }
}

const courseCodeById = (courseId) => {
  const match = courses.value.find((course) => course.course_id === courseId)
  return match ? match.course_code : `ID ${courseId}`
}
const termCodeById = (termId) => {
  const match = terms.value.find((term) => term.term_id === termId)
  return match ? match.term_code : `ID ${termId}`
}
const userLabelById = (userId) => {
  const match = users.value.find((user) => user.user_id === userId)
  if (!match) return userId
  return `${match.username} (${match.email})`
}

onMounted(loadSections)
</script>

<template>
  <div>
    <div class="admin-page-header">
      <h1>Sections</h1>
      <button class="admin-btn-add" @click="openCreate">+ Add Section</button>
    </div>

    <div v-if="error" class="admin-error">{{ error }}</div>
    <div v-if="loading" class="admin-loading">Loading sections...</div>

    <div v-else class="admin-table-card">
      <div class="admin-record-count">{{ total }} section(s)</div>
      <table class="admin-table">
        <thead>
          <tr>
            <th>Section</th>
            <th>Course</th>
            <th>Term</th>
            <th>Capacity</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="section in sections" :key="section.section_id">
            <td class="cell-primary">{{ section.section_number }}</td>
            <td>{{ courseCodeById(section.course_id) }}</td>
            <td>{{ termCodeById(section.term_id) }}</td>
            <td>{{ section.enrolled_count }} / {{ section.max_capacity }}</td>
            <td>{{ section.status }}</td>
            <td>
              <button class="admin-action-btn admin-action-edit" @click="openEdit(section)">Edit</button>
              <button class="admin-action-btn admin-action-delete"
                @click="removeSection(section.section_id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showModal" class="admin-modal-overlay">
      <div class="admin-modal admin-modal-xl">
        <h2>{{ editingSectionId ? 'Edit Section' : 'Create Section' }}</h2>
        <form class="admin-form-grid" @submit.prevent="saveSection">
          <div>
            <label class="form-label">Course</label>
            <select v-model="form.course_id" required>
              <option value="" disabled>Select course</option>
              <option v-for="course in courses" :key="course.course_id" :value="String(course.course_id)">{{
                course.course_code }} - {{ course.course_name }}</option>
            </select>
          </div>
          <div>
            <label class="form-label">Term</label>
            <select v-model="form.term_id" required>
              <option value="" disabled>Select term</option>
              <option v-for="term in terms" :key="term.term_id" :value="String(term.term_id)">{{ term.term_code }} - {{
                term.term_name }}</option>
            </select>
          </div>
          <div><label class="form-label">Section Number</label><input v-model="form.section_number" required /></div>
          <div>
            <label class="form-label">Instructor</label>
            <select v-model="form.instructor_id">
              <option value="">No instructor</option>
              <option v-for="user in users" :key="user.user_id" :value="String(user.user_id)">{{
                userLabelById(user.user_id) }}</option>
            </select>
          </div>
          <div><label class="form-label">Max Capacity</label><input v-model.number="form.max_capacity" type="number"
              min="1" required /></div>
          <div><label class="form-label">Room ID</label><input v-model="form.room_id" type="number" min="1" /></div>
          <div><label class="form-label">Schedule Pattern</label><input v-model="form.schedule_pattern"
              placeholder="MWF" /></div>
          <div>
            <label class="form-label">Delivery Mode</label>
            <select v-model="form.delivery_mode">
              <option value="in-person">In-Person</option>
              <option value="online">Online</option>
              <option value="hybrid">Hybrid</option>
              <option value="hyflex">HyFlex</option>
            </select>
          </div>
          <div><label class="form-label">Start Time</label><input v-model="form.start_time" type="time" /></div>
          <div><label class="form-label">End Time</label><input v-model="form.end_time" type="time" /></div>
          <div><label class="form-label">Start Date</label><input v-model="form.start_date" type="date" /></div>
          <div><label class="form-label">End Date</label><input v-model="form.end_date" type="date" /></div>
          <div><label class="form-label">Meeting URL</label><input v-model="form.meeting_url" /></div>
          <div><label class="form-label">Syllabus URL</label><input v-model="form.syllabus_url" /></div>
          <div>
            <label class="form-label">Status</label>
            <select v-model="form.status">
              <option value="planned">Planned</option>
              <option value="open">Open</option>
              <option value="closed">Closed</option>
              <option value="cancelled">Cancelled</option>
              <option value="full">Full</option>
            </select>
          </div>
          <div class="admin-form-actions">
            <button type="button" class="admin-btn-cancel" @click="closeModal">Cancel</button>
            <button :disabled="saving" type="submit" class="admin-btn-save">{{ saving ? 'Saving...' : 'Save' }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
