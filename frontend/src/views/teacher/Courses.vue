<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  getFacultySections, createSection, updateSection, deleteSection, getCourses, getTerms,
  enrollStudent, getStudents, getSectionEnrollments
} from '../../services/api.js'
import { useToast } from '../../composables/useToast'

const toast = useToast()
import { useAuthStore } from '../../stores/auth'
import Icons from '../../components/icon/Icons.vue'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(true)
const sections = ref([])
const courses = ref([])
const terms = ref([])
const deliveryModeOptions = [
  { value: 'in-person', label: 'In-Person' },
  { value: 'online', label: 'Online' },
  { value: 'hybrid', label: 'Hybrid' },
]

const showModal = ref(false)
const modalMode = ref('create')
const editingId = ref(null)
const formData = ref({
  course_id: '', term_id: '', section_number: '', max_capacity: 30,
  schedule_pattern: '', delivery_mode: 'in-person', room_id: null
})

// Add Student modal
const showAddStudentModal = ref(false)
const addStudentSectionId = ref(null)
const addStudentSectionName = ref('')
const studentSearchQuery = ref('')
const studentSearchType = ref('all') // 'all', 'name', 'username', 'student_number'
const studentResults = ref([])
const studentSearchLoading = ref(false)
const selectedStudentId = ref(null)
const addStudentLoading = ref(false)
let studentSearchTimeout = null
const searchTypeOptions = [
  { value: 'all', label: 'All Fields' },
  { value: 'name', label: 'Name' },
  { value: 'username', label: 'Username' },
  { value: 'student_number', label: 'Student Number' }
]

// Class Detail modal
const showDetailModal = ref(false)
const detailSection = ref(null)
const detailEnrollments = ref([])
const detailLoading = ref(false)
const detailTotal = ref(0)

const searchStudents = async () => {
  if (studentSearchTimeout) clearTimeout(studentSearchTimeout)
  if (!studentSearchQuery.value || studentSearchQuery.value.length < 2) { studentResults.value = []; return }
  studentSearchTimeout = setTimeout(async () => {
    studentSearchLoading.value = true
    try {
      let res
      if (studentSearchType.value === 'all') {
        res = await getStudents(0, 20, null, null, null, studentSearchQuery.value)
      } else if (studentSearchType.value === 'name') {
        res = await getStudents(0, 20, null, null, null, null, studentSearchQuery.value)
      } else if (studentSearchType.value === 'username') {
        res = await getStudents(0, 20, null, null, null, null, null, studentSearchQuery.value)
      } else if (studentSearchType.value === 'student_number') {
        res = await getStudents(0, 20, null, null, null, null, null, null, studentSearchQuery.value)
      }
      studentResults.value = res.data.students || []
    } catch (err) { console.error('Error searching students:', err) }
    finally { studentSearchLoading.value = false }
  }, 300)
}

const openAddStudent = (section) => {
  addStudentSectionId.value = section.section_id
  addStudentSectionName.value = `${section.course?.course_code} - ${section.section_number}`
  studentSearchQuery.value = ''
  studentSearchType.value = 'all'
  studentResults.value = []
  selectedStudentId.value = null
  showAddStudentModal.value = true
}

const handleAddStudent = async () => {
  if (!selectedStudentId.value) return
  addStudentLoading.value = true
  try {
    await enrollStudent(addStudentSectionId.value, selectedStudentId.value)
    toast.success('Student added to class!')
    showAddStudentModal.value = false
    await fetchSections()
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Failed to add student')
  } finally { addStudentLoading.value = false }
}

const copyJoinCode = (code) => {
  navigator.clipboard.writeText(code)
  toast.success('Join code copied!')
}

const fetchDropdowns = async () => {
  try {
    const [coursesRes, termsRes] = await Promise.all([
      getCourses(0, 100, null, null, true),
      getTerms(0, 100, null, null, 'active')
    ])
    courses.value = coursesRes.data.courses || []
    terms.value = termsRes.data.terms || []
    if (terms.value.length === 0) {
      const upcoming = await getTerms(0, 100, null, null, 'upcoming')
      terms.value = upcoming.data.terms || []
    }
  } catch (err) { console.error('Error fetching dropdowns:', err) }
}

const fetchSections = async () => {
  loading.value = true
  try {
    const response = await getFacultySections('me')
    sections.value = response.data.sections || []
  } catch (error) { console.error('Error fetching teacher courses:', error) }
  finally { loading.value = false }
}

onMounted(() => { fetchSections(); fetchDropdowns() })

const handleCreateClasses = () => {
  modalMode.value = 'create'
  formData.value = { course_id: '', term_id: terms.value[0]?.term_id || '', section_number: '', max_capacity: 30, schedule_pattern: '', delivery_mode: 'in-person', room_id: null }
  showModal.value = true
}

const handleEditClass = (section) => {
  modalMode.value = 'edit'
  editingId.value = section.section_id
  formData.value = {
    course_id: section.course_id,
    term_id: section.term_id,
    section_number: section.section_number,
    max_capacity: section.max_capacity,
    schedule_pattern: section.schedule_pattern,
    delivery_mode: (section.delivery_mode || 'in-person').toLowerCase(),
    room_id: section.room_id,
  }
  showModal.value = true
}

const handleDeleteClass = async (id) => {
  if (!confirm('Are you sure you want to delete this class?')) return
  try { await deleteSection(id); toast.success('Class deleted'); await fetchSections() }
  catch (err) { toast.error('Failed to delete section') }
}

const saveClass = async () => {
  try {
    const payload = { ...formData.value, max_capacity: parseInt(formData.value.max_capacity), course_id: parseInt(formData.value.course_id), term_id: parseInt(formData.value.term_id) }
    if (modalMode.value === 'create') { payload.instructor_id = authStore.user.user_id; await createSection(payload); toast.success('Class created') }
    else { await updateSection(editingId.value, payload); toast.success('Class updated') }
    showModal.value = false; await fetchSections()
  } catch (error) { toast.error('Failed to save: ' + (error.response?.data?.detail || error.message)) }
}

const enrollPercent = (sec) => sec.max_capacity ? Math.round((sec.enrolled_count / sec.max_capacity) * 100) : 0

const openClassDetail = async (section) => {
  detailSection.value = section
  detailEnrollments.value = []
  detailTotal.value = 0
  showDetailModal.value = true
  detailLoading.value = true
  try {
    const res = await getSectionEnrollments(section.section_id)
    detailEnrollments.value = res.data.enrollments || []
    detailTotal.value = res.data.total || 0
  } catch (err) {
    console.error('Error fetching enrollments:', err)
  } finally {
    detailLoading.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

const getStudentName = (enr) => {
  const pi = enr.student?.user?.personal_info
  if (pi?.first_name) return `${pi.first_name} ${pi.last_name || ''}`
  return enr.student?.user?.username || 'Unknown'
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
      <div>
        <h1 class="text-2xl font-bold text-ink tracking-tight">My Classes</h1>
        <p class="text-sm text-ink-muted mt-0.5">Manage your course sections</p>
      </div>
      <button @click="handleCreateClasses"
        class="inline-flex items-center gap-2 px-5 py-2.5 bg-coral text-white border-none rounded-xl font-sans text-sm font-medium cursor-pointer transition-all duration-200 hover:bg-coral-hover hover:shadow-[0_4px_12px_rgba(224,122,95,0.3)]">
        <Icons name="mdi-plus" /> Create Class
      </button>
    </div>

    <div v-if="loading" class="text-center py-16 text-ink-muted">
      <Icons name="mdi-loading" class="animate-spin w-8 h-8 mb-2" />
      <p>Loading your classes...</p>
    </div>

    <div v-else-if="sections.length === 0"
      class="bg-surface border border-border-light rounded-2xl shadow-card text-center py-12 text-ink-muted">
      <Icons name="mdi-book-off-outline" class="w-12 h-12 mb-2" />
      <p class="font-medium">No assigned classes found</p>
      <p class="text-xs mt-1">Click "Create Class" to add a new section.</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
      <div v-for="(section, i) in sections" :key="section.section_id"
        class="bg-surface border border-border-light rounded-2xl shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 overflow-hidden animate-fade-in"
        :class="'delay-' + Math.min(i + 1, 4)">
        <!-- Accent stripe -->
        <div class="h-1 bg-primary"></div>
        <div class="p-6">
          <!-- Top -->
          <div class="flex justify-between items-start mb-4">
            <div>
              <span class="inline-block px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary mb-2">{{
                section.course?.course_code }}</span>
              <h3 class="text-base font-semibold text-ink m-0 leading-snug line-clamp-1">{{ section.course?.course_name
              }}</h3>
            </div>
            <div class="flex gap-1">
              <button @click="handleEditClass(section)"
                class="w-8 h-8 border-none rounded-lg bg-transparent text-ink-muted cursor-pointer text-base flex items-center justify-center transition-all hover:bg-info/8 hover:text-info">
                <Icons name="mdi-pencil" />
              </button>
              <button @click="handleDeleteClass(section.section_id)"
                class="w-8 h-8 border-none rounded-lg bg-transparent text-ink-muted cursor-pointer text-base flex items-center justify-center transition-all hover:bg-error/8 hover:text-error">
                <Icons name="mdi-delete" />
              </button>
            </div>
          </div>

          <!-- Join Code -->
          <div class="flex items-center gap-2 px-1 py-1.5 mb-4 bg-page rounded-lg">
            <span class="text-xs text-ink-muted font-medium ml-2">Class Code:</span>
            <code
              class="text-sm font-bold text-primary tracking-widest select-all">{{ section.join_code || '—' }}</code>
            <button v-if="section.join_code" @click="copyJoinCode(section.join_code)"
              class="ml-auto w-7 h-7 border-none rounded-md bg-transparent text-ink-muted cursor-pointer text-sm flex items-center justify-center transition-all hover:bg-primary/10 hover:text-primary"
              title="Copy code">
              <Icons name="mdi-content-copy" />
            </button>
          </div>

          <!-- Details -->
          <div class="flex flex-col gap-2 mb-5">
            <div class="flex items-center gap-2 text-[0.82rem] text-ink-secondary">
              <Icons name="mdi-calendar-clock" class="text-base text-sage" />
              <span>{{ section.schedule_pattern || 'TBA' }}</span>
            </div>
            <div class="flex items-center gap-2 text-[0.82rem] text-ink-secondary">
              <Icons name="mdi-map-marker" class="text-base text-sage" />
              <span>Room {{ section.room_id || 'TBA' }}</span>
            </div>
            <div class="flex items-center gap-2 text-[0.82rem] text-ink-secondary">
              <Icons name="mdi-broadcast" class="text-base text-sage" />
              <span>{{ section.delivery_mode || 'In-Person' }}</span>
            </div>
          </div>

          <!-- Enrollment -->
          <div class="mb-5">
            <div class="flex justify-between items-center mb-1.5">
              <span class="text-xs text-ink-muted font-medium">Enrollment</span>
              <span class="text-xs font-semibold text-ink">{{ section.enrolled_count }} / {{ section.max_capacity
              }}</span>
            </div>
            <div class="w-full h-1 bg-border-light rounded-full overflow-hidden">
              <div class="h-full bg-primary rounded-full transition-all duration-500"
                :style="{ width: enrollPercent(section) + '%' }"></div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex gap-2">
            <button @click="openClassDetail(section)"
              class="flex-1 inline-flex items-center justify-center gap-1.5 px-4 py-2 bg-primary text-white border-none rounded-xl font-sans text-xs font-medium cursor-pointer transition-all hover:bg-primary-light hover:shadow-[0_4px_12px_rgba(47,79,79,0.25)]">
              <Icons name="mdi-eye" /> View Details
            </button>
            <router-link :to="{ name: 'TeacherGrades', query: { sectionId: section.section_id } }"
              class="flex-1 inline-flex items-center justify-center gap-1.5 px-4 py-2 bg-transparent text-primary border-[1.5px] border-primary/30 rounded-xl font-sans text-xs font-medium no-underline cursor-pointer transition-all hover:bg-primary/8 hover:border-primary">
              <Icons name="mdi-chart-bar" /> Grades
            </router-link>
          </div>
          <div class="flex gap-2 mt-2">
            <button @click="openAddStudent(section)"
              class="flex-1 inline-flex items-center justify-center gap-1.5 px-4 py-2 bg-transparent text-coral border-[1.5px] border-coral/30 rounded-xl font-sans text-xs font-medium cursor-pointer transition-all hover:bg-coral/8 hover:border-coral">
              <Icons name="mdi-account-plus" /> Add Student
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-ink/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="showModal = false">
      <div class="bg-surface rounded-2xl shadow-modal w-full max-w-120 overflow-hidden animate-fade-in">
        <div class="flex items-center justify-between px-6 py-5 border-b border-border-light bg-page">
          <h3 class="text-lg font-semibold text-ink m-0">{{ modalMode === 'create' ? 'Create Class' : 'Edit Class' }}
          </h3>
          <button @click="showModal = false"
            class="w-8 h-8 border-none rounded-lg bg-transparent text-ink-muted cursor-pointer text-base flex items-center justify-center hover:bg-primary/5">
            <Icons name="mdi-close" />
          </button>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <label class="block text-xs font-medium text-ink-secondary mb-1.5">Course</label>
            <select v-model="formData.course_id"
              class="w-full px-3.5 py-2.5 text-sm font-sans border-[1.5px] border-border-medium rounded-xl bg-surface text-ink transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.12)]">
              <option value="" disabled>Select Course</option>
              <option v-for="c in courses" :key="c.course_id" :value="c.course_id">{{ c.course_code }} — {{
                c.course_name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-ink-secondary mb-1.5">Term</label>
            <select v-model="formData.term_id"
              class="w-full px-3.5 py-2.5 text-sm font-sans border-[1.5px] border-border-medium rounded-xl bg-surface text-ink transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.12)]">
              <option value="" disabled>Select Term</option>
              <option v-for="t in terms" :key="t.term_id" :value="t.term_id">{{ t.term_name }} ({{ t.academic_year }})
              </option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-ink-secondary mb-1.5">Section Number</label>
            <input v-model="formData.section_number" type="text" placeholder="e.g. 001"
              class="w-full px-3.5 py-2.5 text-sm font-sans border-[1.5px] border-border-medium rounded-xl bg-surface text-ink transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.12)]" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-ink-secondary mb-1.5">Capacity</label>
              <input v-model="formData.max_capacity" type="number"
                class="w-full px-3.5 py-2.5 text-sm font-sans border-[1.5px] border-border-medium rounded-xl bg-surface text-ink transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.12)]" />
            </div>
            <div>
              <label class="block text-xs font-medium text-ink-secondary mb-1.5">Delivery</label>
              <select v-model="formData.delivery_mode"
                class="w-full px-3.5 py-2.5 text-sm font-sans border-[1.5px] border-border-medium rounded-xl bg-surface text-ink transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.12)]">
                <option v-for="mode in deliveryModeOptions" :key="mode.value" :value="mode.value">{{ mode.label }}</option>
              </select>
            </div>
          </div>
          <div>
            <label class="block text-xs font-medium text-ink-secondary mb-1.5">Schedule (e.g. MWF 10:00-11:00)</label>
            <input v-model="formData.schedule_pattern" type="text"
              class="w-full px-3.5 py-2.5 text-sm font-sans border-[1.5px] border-border-medium rounded-xl bg-surface text-ink transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.12)]" />
          </div>
        </div>
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-border-light bg-page">
          <button @click="showModal = false"
            class="inline-flex items-center gap-2 px-4 py-2 bg-transparent text-primary border-[1.5px] border-border-medium rounded-xl font-sans text-sm font-medium cursor-pointer transition-all hover:border-primary hover:bg-primary/5">
            Cancel
          </button>
          <button @click="saveClass"
            class="inline-flex items-center gap-2 px-5 py-2 bg-coral text-white border-none rounded-xl font-sans text-sm font-medium cursor-pointer transition-all duration-200 hover:bg-coral-hover hover:shadow-[0_4px_12px_rgba(224,122,95,0.3)]">
            Save
          </button>
        </div>
      </div>
    </div>

    <!-- Add Student Modal -->
    <div v-if="showAddStudentModal"
      class="fixed inset-0 bg-ink/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="showAddStudentModal = false">
      <div class="bg-surface rounded-2xl shadow-modal w-full max-w-md overflow-hidden animate-fade-in">
        <div class="flex items-center justify-between px-6 py-5 border-b border-border-light bg-page">
          <div>
            <h3 class="text-lg font-semibold text-ink m-0">Add Student</h3>
            <p class="text-xs text-ink-muted mt-0.5">{{ addStudentSectionName }}</p>
          </div>
          <button @click="showAddStudentModal = false"
            class="w-8 h-8 border-none rounded-lg bg-transparent text-ink-muted cursor-pointer text-base flex items-center justify-center hover:bg-primary/5">
            <Icons name="mdi-close" />
          </button>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <label class="block text-xs font-medium text-ink-secondary mb-1.5">Search Student</label>
            <div class="flex gap-2">
              <select v-model="studentSearchType"
                class="px-3 py-2.5 text-sm font-sans border-[1.5px] border-border-medium rounded-xl bg-surface text-ink transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.12)]">
                <option v-for="opt in searchTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
              <input v-model="studentSearchQuery" type="text" placeholder="Type to search..."
                @input="searchStudents"
                @keyup.enter="searchStudents"
                class="flex-1 px-3.5 py-2.5 text-sm font-sans border-[1.5px] border-border-medium rounded-xl bg-surface text-ink transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.12)]" />
              <button @click="searchStudents"
                class="px-4 py-2.5 bg-primary text-white border-none rounded-xl text-sm font-medium cursor-pointer transition-all hover:bg-primary-light">
                <Icons name="mdi-magnify" />
              </button>
            </div>
          </div>

          <!-- Student Results -->
          <div v-if="studentSearchLoading" class="text-center py-4 text-ink-muted text-sm">
            <Icons name="mdi-loading" class="animate-spin w-5 h-5 mb-1" />
            <p>Searching...</p>
          </div>
          <div v-else-if="studentResults.length > 0"
            class="max-h-48 overflow-y-auto border border-border-light rounded-xl">
            <label v-for="s in studentResults" :key="s.student_id"
              class="flex items-center gap-3 px-4 py-3 border-b border-border-light last:border-b-0 cursor-pointer transition-colors"
              :class="selectedStudentId === s.student_id ? 'bg-primary/8' : 'hover:bg-page'">
              <input type="radio" :value="s.student_id" v-model="selectedStudentId" class="accent-primary w-4 h-4" />
              <div>
                <p class="text-sm font-medium text-ink">{{ s.user?.personal_info?.first_name }} {{
                  s.user?.personal_info?.last_name }}</p>
                <p class="text-xs text-ink-muted">{{ s.user?.username }} · {{ s.student_number || 'No ID' }}</p>
              </div>
            </label>
          </div>
          <div v-else-if="studentSearchQuery.length >= 2 && !studentSearchLoading"
            class="text-center py-4 text-ink-muted text-sm">
            No students found.
          </div>
        </div>
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-border-light bg-page">
          <button @click="showAddStudentModal = false"
            class="inline-flex items-center gap-2 px-4 py-2 bg-transparent text-primary border-[1.5px] border-border-medium rounded-xl font-sans text-sm font-medium cursor-pointer transition-all hover:border-primary hover:bg-primary/5">
            Cancel
          </button>
          <button @click="handleAddStudent" :disabled="!selectedStudentId || addStudentLoading"
            class="inline-flex items-center gap-2 px-5 py-2 bg-coral text-white border-none rounded-xl font-sans text-sm font-medium cursor-pointer transition-all duration-200 hover:bg-coral-hover hover:shadow-[0_4px_12px_rgba(224,122,95,0.3)] disabled:opacity-50 disabled:cursor-not-allowed">
            {{ addStudentLoading ? 'Adding...' : 'Add Student' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Class Detail Modal -->
    <div v-if="showDetailModal"
      class="fixed inset-0 bg-ink/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="showDetailModal = false">
      <div
        class="bg-surface rounded-2xl shadow-modal w-full max-w-2xl max-h-[85vh] overflow-hidden animate-fade-in flex flex-col">
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-5 border-b border-border-light bg-page shrink-0">
          <div>
            <h3 class="text-lg font-semibold text-ink m-0">Class Details</h3>
            <p class="text-xs text-ink-muted mt-0.5">{{ detailSection?.course?.course_code }} — {{
              detailSection?.course?.course_name }}</p>
          </div>
          <button @click="showDetailModal = false"
            class="w-8 h-8 border-none rounded-lg bg-transparent text-ink-muted cursor-pointer text-base flex items-center justify-center hover:bg-primary/5">
            <Icons name="mdi-close" />
          </button>
        </div>

        <!-- Content -->
        <div class="overflow-y-auto flex-1 p-6 space-y-5">
          <!-- Info Grid -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div class="bg-page rounded-xl p-3.5 text-center">
              <p class="text-2xl font-bold text-primary">{{ detailSection?.enrolled_count || 0 }}</p>
              <p class="text-[0.7rem] text-ink-muted font-medium uppercase tracking-wide mt-1">Students</p>
            </div>
            <div class="bg-page rounded-xl p-3.5 text-center">
              <p class="text-2xl font-bold text-ink">{{ detailSection?.max_capacity || 0 }}</p>
              <p class="text-[0.7rem] text-ink-muted font-medium uppercase tracking-wide mt-1">Capacity</p>
            </div>
            <div class="bg-page rounded-xl p-3.5 text-center">
              <p class="text-2xl font-bold" :class="enrollPercent(detailSection) >= 90 ? 'text-coral' : 'text-success'">
                {{ enrollPercent(detailSection) }}%</p>
              <p class="text-[0.7rem] text-ink-muted font-medium uppercase tracking-wide mt-1">Filled</p>
            </div>
            <div class="bg-page rounded-xl p-3.5 text-center">
              <p class="text-2xl font-bold text-sage">{{ (detailSection?.max_capacity || 0) -
                (detailSection?.enrolled_count || 0) }}</p>
              <p class="text-[0.7rem] text-ink-muted font-medium uppercase tracking-wide mt-1">Seats Left</p>
            </div>
          </div>

          <!-- Section Info -->
          <div class="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <div class="flex items-center gap-2 text-ink-secondary">
              <Icons name="mdi-identifier" class="text-base text-sage" />
              <span>Section {{ detailSection?.section_number }}</span>
            </div>
            <div class="flex items-center gap-2 text-ink-secondary">
              <Icons name="mdi-calendar-clock" class="text-base text-sage" />
              <span>{{ detailSection?.schedule_pattern || 'TBA' }}</span>
            </div>
            <div class="flex items-center gap-2 text-ink-secondary">
              <Icons name="mdi-broadcast" class="text-base text-sage" />
              <span>{{ detailSection?.delivery_mode || 'In-Person' }}</span>
            </div>
            <div class="flex items-center gap-2 text-ink-secondary">
              <Icons name="mdi-key-variant" class="text-base text-sage" />
              <code class="font-bold text-primary tracking-wider">{{ detailSection?.join_code || '—' }}</code>
            </div>
          </div>

          <!-- Enrolled Students -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <h4 class="text-sm font-semibold text-ink m-0 flex items-center gap-2">
                <Icons name="mdi-account-group" class="text-base text-primary" /> Enrolled Students
              </h4>
              <span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">{{ detailTotal }}
                total</span>
            </div>

            <div v-if="detailLoading" class="text-center py-8 text-ink-muted">
              <Icons name="mdi-loading" class="animate-spin w-6 h-6 mb-2" />
              <p class="text-sm">Loading students...</p>
            </div>

            <div v-else-if="detailEnrollments.length === 0" class="text-center py-8 text-ink-muted">
              <Icons name="mdi-account-off-outline" class="w-10 h-10 mb-2" />
              <p class="text-sm">No students enrolled yet.</p>
            </div>

            <div v-else class="border border-border-light rounded-xl overflow-hidden">
              <!-- Table header -->
              <div
                class="grid grid-cols-[2fr_1fr_1fr_auto] bg-page px-4 py-2.5 text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                <span>Student</span>
                <span>Student ID</span>
                <span>Enrolled</span>
                <span>Status</span>
              </div>
              <!-- Rows -->
              <div v-for="enr in detailEnrollments" :key="enr.enrollment_id"
                class="grid grid-cols-[2fr_1fr_1fr_auto] items-center px-4 py-3 border-b border-border-light last:border-b-0 hover:bg-page/60 transition-colors">
                <div class="flex items-center gap-2.5">
                  <div
                    class="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold shrink-0">
                    {{ getStudentName(enr).charAt(0) }}
                  </div>
                  <div>
                    <p class="text-sm font-medium text-ink leading-tight">{{ getStudentName(enr) }}</p>
                    <p class="text-[0.7rem] text-ink-muted">{{ enr.student?.user?.email || '' }}</p>
                  </div>
                </div>
                <span class="text-sm text-ink-secondary font-mono">{{ enr.student?.student_number || '—' }}</span>
                <span class="text-xs text-ink-muted">{{ formatDate(enr.enrollment_date) }}</span>
                <span class="px-2.5 py-1 rounded-full text-[0.65rem] font-semibold"
                  :class="enr.enrollment_status === 'enrolled' ? 'bg-success/12 text-[#047857]' : 'bg-slate-100 text-slate-500'">
                  {{ enr.enrollment_status }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-between px-6 py-4 border-t border-border-light bg-page shrink-0">
          <button @click="openAddStudent(detailSection); showDetailModal = false"
            class="inline-flex items-center gap-2 px-4 py-2 bg-transparent text-coral border-[1.5px] border-coral/30 rounded-xl font-sans text-sm font-medium cursor-pointer transition-all hover:bg-coral/8 hover:border-coral">
            <Icons name="mdi-account-plus" /> Add Student
          </button>
          <button @click="showDetailModal = false"
            class="inline-flex items-center gap-2 px-5 py-2 bg-primary text-white border-none rounded-xl font-sans text-sm font-medium cursor-pointer transition-all hover:bg-primary-light">
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>