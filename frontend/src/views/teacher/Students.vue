<<<<<<< HEAD
<script setup>
import { ref, onMounted, watch } from 'vue'
import { getFacultySections, getSectionEnrollments } from '../../services/api.js'
import { useAuthStore } from '../../stores/auth'
import Icons from '../../components/icon/Icons.vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const authStore = useAuthStore()
const loading = ref(true)
const enrollmentsLoading = ref(false)
const sections = ref([])
const selectedSectionId = ref('all')
const students = ref([])
const searchQuery = ref('')
let searchTimeout = null

onMounted(async () => {
  if (!authStore.user?.user_id) { loading.value = false; return }
  loading.value = true
  try {
    const response = await getFacultySections('me')
    sections.value = response.data.sections || []
    const querySectionId = route.query.sectionId
    if (querySectionId && sections.value.some(s => s.section_id === Number(querySectionId))) {
      selectedSectionId.value = Number(querySectionId)
      await fetchSectionStudents(Number(querySectionId))
    } else {
      await fetchAllStudents()
    }
  } catch (error) { console.error('Error fetching teacher sections:', error) }
  finally { loading.value = false }
})

const fetchAllStudents = async () => {
  enrollmentsLoading.value = true; students.value = []
  try {
    const results = await Promise.all(sections.value.map(s => getSectionEnrollments(s.section_id, searchQuery.value)))
    const all = []
    results.forEach((res, i) => { res.data.enrollments.forEach(enr => all.push({ ...enr, section_info: sections.value[i] })) })
    students.value = all
  } catch (error) { console.error('Error:', error) }
  finally { enrollmentsLoading.value = false }
}

const fetchSectionStudents = async (sectionId) => {
  enrollmentsLoading.value = true
  try {
    const response = await getSectionEnrollments(sectionId, searchQuery.value)
    const section = sections.value.find(s => s.section_id === sectionId)
    students.value = (response.data.enrollments || []).map(enr => ({ ...enr, section_info: section }))
  } catch (error) { console.error('Error:', error) }
  finally { enrollmentsLoading.value = false }
}

watch(selectedSectionId, (newId) => {
  if (newId === 'all') fetchAllStudents();
  else fetchSectionStudents(newId)
})

watch(searchQuery, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    if (selectedSectionId.value === 'all') fetchAllStudents()
    else fetchSectionStudents(selectedSectionId.value)
  }, 300)
})

const getAverage = (enr) => {
  if (enr.final_grade) return enr.final_grade
  if (enr.midterm_grade) return enr.midterm_grade + ' (M)'
  return '—'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
      <div>
        <h1 class="text-2xl font-bold text-ink tracking-tight">Student Directory</h1>
        <p class="text-sm text-ink-muted mt-0.5">Managing students across your assigned sections</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="relative">
          <Icons name="mdi-magnify" class="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted text-lg" />
          <input type="text" v-model="searchQuery" placeholder="Search students..."
            class="pl-10 pr-4 py-2 bg-surface border border-border-light rounded-xl text-sm text-ink focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20 w-48 transition-all" />
        </div>
        <div
          class="flex items-center gap-2 bg-surface border border-border-light rounded-xl shadow-card pl-3 pr-1 py-1">
          <Icons name="mdi-filter-variant" class="text-ink-muted text-lg" />
          <select v-model="selectedSectionId"
            class="border-none bg-transparent text-sm text-ink font-sans py-2 pr-8 focus:outline-none cursor-pointer">
            <option value="all">All Sections</option>
            <option v-for="section in sections" :key="section.section_id" :value="section.section_id">
              {{ section.course?.course_code }} — Sec {{ section.section_number }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Table Card -->
    <div class="bg-surface border border-border-light rounded-2xl shadow-card animate-fade-in">
      <!-- Loading -->
      <div v-if="loading" class="text-center py-12 text-ink-muted">
        <Icons name="mdi-loading" class="animate-spin w-8 h-8 mb-2" />
        <p>Initializing directory...</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full border-collapse">
          <thead class="bg-page">
            <tr>
              <th
                class="px-6 py-3.5 text-left text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Student Name
              </th>
              <th
                class="px-6 py-3.5 text-left text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Student ID
              </th>
              <th
                class="px-6 py-3.5 text-left text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Course Section
              </th>
              <th
                class="px-6 py-3.5 text-center text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Attendance
              </th>
              <th
                class="px-6 py-3.5 text-center text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Current Grade
              </th>
              <th
                class="px-6 py-3.5 text-right text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="enrollmentsLoading">
              <td colspan="6" class="px-6 py-6 text-center text-ink-muted italic">Updating list...</td>
            </tr>
            <tr v-else-if="students.length === 0">
              <td colspan="6" class="text-center py-12 text-ink-muted">
                <Icons name="mdi-account-search-outline" class="w-12 h-12 mb-2 text-border-medium" />
                <p>No students found in this selection.</p>
              </td>
            </tr>
            <tr v-for="enr in students" :key="enr.enrollment_id + '-' + enr.section_id"
              class="border-b border-border-light last:border-b-0 hover:bg-primary/0.25 transition-colors">
              <td class="px-6 py-3.5">
                <div class="flex items-center">
                  <div
                    class="w-9 h-9 rounded-full bg-primary/10 text-primary text-xs font-semibold flex items-center justify-center shrink-0">
                    {{ enr.student?.user?.personal_info?.first_name?.[0] }}{{
                      enr.student?.user?.personal_info?.last_name?.[0] }}
                  </div>
                  <div class="ml-3">
                    <p class="font-medium text-sm text-ink">{{ enr.student?.user?.personal_info?.first_name }} {{
                      enr.student?.user?.personal_info?.last_name }}</p>
                    <p class="text-[0.72rem] text-ink-muted">{{ enr.student?.user?.email }}</p>
                  </div>
                </div>
              </td>
              <td class="px-6 py-3.5 font-mono text-sm text-ink-secondary">{{ enr.student?.student_number }}</td>
              <td class="px-6 py-3.5">
                <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary">{{
                  enr.section_info?.course?.course_code }}</span>
                <span class="ml-2 text-xs text-ink-muted">Sec {{ enr.section_info?.section_number }}</span>
              </td>
              <td class="px-6 py-3.5 text-center">
                <div class="inline-flex flex-col items-center">
                  <span class="text-sm font-semibold"
                    :class="(enr.attendance_percentage || 0) >= 90 ? 'text-success' : 'text-warning'">
                    {{ enr.attendance_percentage || '—' }}%
                  </span>
                  <div class="w-16 h-1 bg-border-light rounded-full overflow-hidden mt-1">
                    <div class="h-full rounded-full transition-all duration-500"
                      :class="(enr.attendance_percentage || 0) >= 90 ? 'bg-success' : 'bg-coral'"
                      :style="{ width: (enr.attendance_percentage || 0) + '%' }"></div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-3.5 text-center">
                <span
                  class="inline-flex items-center justify-center px-2.5 py-1 rounded-lg bg-page text-ink font-bold text-sm min-w-10">{{
                    getAverage(enr) }}
                </span>
              </td>
              <td class="px-6 py-3.5 text-right">
                <div class="flex justify-end gap-1">
                  <button
                    class="w-8 h-8 rounded-lg bg-transparent border-none text-ink-muted text-base flex items-center justify-center cursor-pointer transition-all hover:bg-primary/6 hover:text-primary">
                    <Icons name="mdi-eye" />
                  </button>
                  <button
                    class="w-8 h-8 rounded-lg bg-transparent border-none text-ink-muted text-base flex items-center justify-center cursor-pointer transition-all hover:bg-success/6 hover:text-success">
                    <Icons name="mdi-email-outline" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
=======
<script setup>
import { ref, onMounted, watch } from 'vue'
import { getFacultySections, getSectionEnrollments } from '../../services/api.js'
import { useAuthStore } from '../../stores/auth'
import Icons from '../../components/icon/Icons.vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const authStore = useAuthStore()
const loading = ref(true)
const enrollmentsLoading = ref(false)
const sections = ref([])
const selectedSectionId = ref('all')
const students = ref([])
const searchQuery = ref('')
let searchTimeout = null

onMounted(async () => {
  if (!authStore.user?.user_id) { loading.value = false; return }
  loading.value = true
  try {
    const response = await getFacultySections(authStore.user.user_id)
    sections.value = response.data.sections || []
    const querySectionId = route.query.sectionId
    if (querySectionId && sections.value.some(s => s.section_id === Number(querySectionId))) {
      selectedSectionId.value = Number(querySectionId)
      await fetchSectionStudents(Number(querySectionId))
    } else {
      await fetchAllStudents()
    }
  } catch (error) { console.error('Error fetching teacher sections:', error) }
  finally { loading.value = false }
})

const fetchAllStudents = async () => {
  enrollmentsLoading.value = true; students.value = []
  try {
    const results = await Promise.all(sections.value.map(s => getSectionEnrollments(s.section_id, searchQuery.value)))
    const all = []
    results.forEach((res, i) => { res.data.enrollments.forEach(enr => all.push({ ...enr, section_info: sections.value[i] })) })
    students.value = all
  } catch (error) { console.error('Error:', error) }
  finally { enrollmentsLoading.value = false }
}

const fetchSectionStudents = async (sectionId) => {
  enrollmentsLoading.value = true
  try {
    const response = await getSectionEnrollments(sectionId, searchQuery.value)
    const section = sections.value.find(s => s.section_id === sectionId)
    students.value = (response.data.enrollments || []).map(enr => ({ ...enr, section_info: section }))
  } catch (error) { console.error('Error:', error) }
  finally { enrollmentsLoading.value = false }
}

watch(selectedSectionId, (newId) => {
  if (newId === 'all') fetchAllStudents();
  else fetchSectionStudents(newId)
})

watch(searchQuery, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    if (selectedSectionId.value === 'all') fetchAllStudents()
    else fetchSectionStudents(selectedSectionId.value)
  }, 300)
})

const getAverage = (enr) => {
  if (enr.final_grade) return enr.final_grade
  if (enr.midterm_grade) return enr.midterm_grade + ' (M)'
  return '—'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
      <div>
        <h1 class="text-2xl font-bold text-ink tracking-tight">Student Directory</h1>
        <p class="text-sm text-ink-muted mt-0.5">Managing students across your assigned sections</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="relative">
          <Icons name="mdi-magnify" class="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted text-lg" />
          <input type="text" v-model="searchQuery" placeholder="Search students..."
            class="pl-10 pr-4 py-2 bg-surface border border-border-light rounded-xl text-sm text-ink focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20 w-48 transition-all" />
        </div>
        <div
          class="flex items-center gap-2 bg-surface border border-border-light rounded-xl shadow-card pl-3 pr-1 py-1">
          <Icons name="mdi-filter-variant" class="text-ink-muted text-lg" />
          <select v-model="selectedSectionId"
            class="border-none bg-transparent text-sm text-ink font-sans py-2 pr-8 focus:outline-none cursor-pointer">
            <option value="all">All Sections</option>
            <option v-for="section in sections" :key="section.section_id" :value="section.section_id">
              {{ section.course?.course_code }} — Sec {{ section.section_number }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Table Card -->
    <div class="bg-surface border border-border-light rounded-2xl shadow-card animate-fade-in">
      <!-- Loading -->
      <div v-if="loading" class="text-center py-12 text-ink-muted">
        <Icons name="mdi-loading" class="animate-spin w-8 h-8 mb-2" />
        <p>Initializing directory...</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full border-collapse">
          <thead class="bg-page">
            <tr>
              <th
                class="px-6 py-3.5 text-left text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Student Name
              </th>
              <th
                class="px-6 py-3.5 text-left text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Student ID
              </th>
              <th
                class="px-6 py-3.5 text-left text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Course Section
              </th>
              <th
                class="px-6 py-3.5 text-center text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Attendance
              </th>
              <th
                class="px-6 py-3.5 text-center text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Current Grade
              </th>
              <th
                class="px-6 py-3.5 text-right text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="enrollmentsLoading">
              <td colspan="6" class="px-6 py-6 text-center text-ink-muted italic">Updating list...</td>
            </tr>
            <tr v-else-if="students.length === 0">
              <td colspan="6" class="text-center py-12 text-ink-muted">
                <Icons name="mdi-account-search-outline" class="w-12 h-12 mb-2 text-border-medium" />
                <p>No students found in this selection.</p>
              </td>
            </tr>
            <tr v-for="enr in students" :key="enr.enrollment_id + '-' + enr.section_id"
              class="border-b border-border-light last:border-b-0 hover:bg-primary/0.25 transition-colors">
              <td class="px-6 py-3.5">
                <div class="flex items-center">
                  <div
                    class="w-9 h-9 rounded-full bg-primary/10 text-primary text-xs font-semibold flex items-center justify-center shrink-0">
                    {{ enr.student?.user?.personal_info?.first_name?.[0] }}{{
                      enr.student?.user?.personal_info?.last_name?.[0] }}
                  </div>
                  <div class="ml-3">
                    <p class="font-medium text-sm text-ink">{{ enr.student?.user?.personal_info?.first_name }} {{
                      enr.student?.user?.personal_info?.last_name }}</p>
                    <p class="text-[0.72rem] text-ink-muted">{{ enr.student?.user?.email }}</p>
                  </div>
                </div>
              </td>
              <td class="px-6 py-3.5 font-mono text-sm text-ink-secondary">{{ enr.student?.student_number }}</td>
              <td class="px-6 py-3.5">
                <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary">{{
                  enr.section_info?.course?.course_code }}</span>
                <span class="ml-2 text-xs text-ink-muted">Sec {{ enr.section_info?.section_number }}</span>
              </td>
              <td class="px-6 py-3.5 text-center">
                <div class="inline-flex flex-col items-center">
                  <span class="text-sm font-semibold"
                    :class="(enr.attendance_percentage || 0) >= 90 ? 'text-success' : 'text-warning'">
                    {{ enr.attendance_percentage || '—' }}%
                  </span>
                  <div class="w-16 h-1 bg-border-light rounded-full overflow-hidden mt-1">
                    <div class="h-full rounded-full transition-all duration-500"
                      :class="(enr.attendance_percentage || 0) >= 90 ? 'bg-success' : 'bg-coral'"
                      :style="{ width: (enr.attendance_percentage || 0) + '%' }"></div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-3.5 text-center">
                <span
                  class="inline-flex items-center justify-center px-2.5 py-1 rounded-lg bg-page text-ink font-bold text-sm min-w-10">{{
                    getAverage(enr) }}
                </span>
              </td>
              <td class="px-6 py-3.5 text-right">
                <div class="flex justify-end gap-1">
                  <button
                    class="w-8 h-8 rounded-lg bg-transparent border-none text-ink-muted text-base flex items-center justify-center cursor-pointer transition-all hover:bg-primary/6 hover:text-primary">
                    <Icons name="mdi-eye" />
                  </button>
                  <button
                    class="w-8 h-8 rounded-lg bg-transparent border-none text-ink-muted text-base flex items-center justify-center cursor-pointer transition-all hover:bg-success/6 hover:text-success">
                    <Icons name="mdi-email-outline" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
>>>>>>> a1077c5da31aaef6385c7850c5580088169ce36c
