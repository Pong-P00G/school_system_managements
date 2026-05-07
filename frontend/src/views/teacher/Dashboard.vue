<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { getFacultyProfile, getFacultySections } from '../../services/api.js'
import Icons from '../../components/icon/Icons.vue'

const authStore = useAuthStore()
const loading = ref(true)
const teacherInfo = ref(null)
const mySections = ref([])

const teacherName = computed(() => teacherInfo.value ? `${teacherInfo.value.user?.personal_info?.first_name} ${teacherInfo.value.user?.personal_info?.last_name}` : 'Instructor')
const deptName = computed(() => teacherInfo.value?.department?.department_name || 'N/A')
const title = computed(() => teacherInfo.value?.faculty_rank || 'Faculty Member')
const totalStudents = computed(() => mySections.value.reduce((total, sec) => total + (sec.enrolled_count || 0), 0))
const activeCourses = computed(() => mySections.value.length)

const pendingTasks = ref([
  { type: 'Grading', item: 'CS201 - Assignment 3', due: '2025-02-18' },
  { type: 'Grading', item: 'CS301 - Quiz 5', due: '2025-02-19' },
  { type: 'Grade Entry', item: 'CS401 - Midterm Exams', due: '2025-02-20' },
])

onMounted(async () => {
  if (!authStore.user?.user_id) { loading.value = false; return }
  loading.value = true
  try {
    const [facultyRes, sectionsRes] = await Promise.allSettled([
      getFacultyProfile(),
      getFacultySections('me')
    ])
    if (facultyRes.status === 'fulfilled') teacherInfo.value = facultyRes.value.data
    if (sectionsRes.status === 'fulfilled') mySections.value = sectionsRes.value.data.sections || []
  } catch (error) {
    console.error('Error fetching teacher data:', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <!-- Welcome Banner -->
    <div class="bg-primary rounded-2xl p-5 sm:p-8 text-white relative overflow-hidden animate-fade-in">
      <div class="absolute -top-[40%] -right-[10%] w-80 h-80 bg-white/6 rounded-full"></div>
      <div class="absolute -bottom-[30%] -left-[5%] w-52 h-52 bg-white/4 rounded-full"></div>
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center relative z-10 gap-4">
        <div>
          <p class="text-sm opacity-75 m-0 mb-0.5">Welcome back,</p>
          <h1 class="text-2xl font-bold m-0 mb-3">{{ teacherName }}</h1>
          <div class="flex gap-2 flex-wrap">
            <span class="px-3 py-1 rounded-full text-xs font-medium bg-white/15">{{ title }}</span>
            <span class="px-3 py-1 rounded-full text-xs font-medium bg-white/15">{{ deptName }}</span>
          </div>
        </div>
        <div class="text-left sm:text-right">
          <p class="text-[2.5rem] font-bold m-0 leading-none">{{ activeCourses }}</p>
          <p class="text-xs opacity-70 uppercase tracking-widest mt-1.5 m-0">Active Courses</p>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-ink-muted">
      <Icons name="mdi-loading" class="animate-spin w-8 h-8 mb-2" />
      <p>Loading dashboard...</p>
    </div>

    <!-- Stats -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div
        class="bg-surface border border-border-light rounded-2xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 relative overflow-hidden animate-fade-in delay-1">
        <div class="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-primary"></div>
        <div class="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center text-lg mb-3">
          <Icons name="mdi-book-open-variant" />
        </div>
        <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Courses Teaching</p>
        <p class="text-3xl font-bold text-ink">{{ activeCourses }}</p>
      </div>
      <div
        class="bg-surface border border-border-light rounded-2xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 relative overflow-hidden animate-fade-in delay-2">
        <div class="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-sage"></div>
        <div class="w-10 h-10 rounded-full bg-sage/12 text-[#5e6e5f] flex items-center justify-center text-lg mb-3">
          <Icons name="mdi-account-group" />
        </div>
        <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Total Students</p>
        <p class="text-3xl font-bold text-ink">{{ totalStudents }}</p>
      </div>
      <div
        class="bg-surface border border-border-light rounded-2xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 relative overflow-hidden animate-fade-in delay-3">
        <div class="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-coral"></div>
        <div class="w-10 h-10 rounded-full bg-coral/12 text-coral flex items-center justify-center text-lg mb-3">
          <Icons name="mdi-clipboard-text-clock" />
        </div>
        <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Pending Grading</p>
        <p class="text-3xl font-bold text-ink">{{ pendingTasks.length }}</p>
      </div>
    </div>

    <!-- My Courses -->
    <div v-if="!loading" class="bg-surface border border-border-light rounded-2xl shadow-card animate-fade-in delay-3">
      <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
        <h3 class="text-base font-semibold text-ink">My Courses</h3>
        <router-link to="/teacher/courses"
          class="text-xs font-medium text-coral no-underline hover:text-coral-hover transition-colors">View All
          →</router-link>
      </div>
      <div>
        <div v-for="section in mySections.slice(0, 4)" :key="section.section_id"
          class="flex flex-col sm:flex-row sm:items-center justify-between px-4 sm:px-6 py-4 border-b border-border-light last:border-b-0 hover:bg-primary/0.25 transition-colors gap-2 sm:gap-0">
          <div class="flex items-center gap-3">
            <div
              class="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center text-lg shrink-0">
              <Icons name="mdi-book-open-variant" />
            </div>
            <div>
              <p class="font-medium text-sm text-ink">{{ section.course?.course_code }} — {{ section.course?.course_name
              }}</p>
              <p class="text-xs text-ink-muted mt-0.5">Section {{ section.section_number }} · {{
                section.schedule_pattern || 'Schedule TBA' }}</p>
            </div>
          </div>
          <span class="px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">{{ section.enrolled_count
          }} enrolled</span>
        </div>
        <div v-if="mySections.length === 0" class="text-center py-10 text-ink-muted">
          <Icons name="mdi-book-off-outline" class="w-10 h-10 mb-2" />
          <p>No active courses found.</p>
        </div>
      </div>
    </div>

    <!-- Pending Tasks -->
    <div v-if="!loading" class="bg-surface border border-border-light rounded-2xl shadow-card animate-fade-in delay-4">
      <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
        <h3 class="text-base font-semibold text-ink">Pending Tasks</h3>
      </div>
      <div>
        <div v-for="task in pendingTasks" :key="task.item"
          class="flex flex-col sm:flex-row sm:items-center justify-between px-4 sm:px-6 py-4 border-b border-border-light last:border-b-0 hover:bg-primary/0.25 transition-colors gap-2 sm:gap-0">
          <div class="flex items-center gap-3">
            <div
              class="w-10 h-10 rounded-full bg-coral/12 text-coral flex items-center justify-center text-lg shrink-0">
              <Icons name="mdi-clipboard-text-clock" />
            </div>
            <div>
              <p class="font-medium text-sm text-ink">{{ task.item }}</p>
              <p class="text-xs text-ink-muted mt-0.5">{{ task.type }}</p>
            </div>
          </div>
          <span class="px-3 py-1 rounded-full text-xs font-medium bg-error/10 text-error">Due: {{ task.due }}</span>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div v-if="!loading"
      class="bg-surface border border-border-light rounded-2xl shadow-card p-6 animate-fade-in delay-4">
      <h3 class="text-base font-semibold text-ink mb-4">Quick Actions</h3>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <router-link to="/teacher/grades"
          class="flex items-center gap-3 p-4 border border-border-light rounded-xl no-underline text-ink text-sm font-medium transition-all duration-200 hover:bg-primary/0.25 hover:border-primary hover:shadow-card">
          <div class="w-10 h-10 rounded-full bg-coral/12 text-coral flex items-center justify-center">
            <Icons name="mdi-pencil" />
          </div>
          <span>Enter Grades</span>
        </router-link>
        <router-link to="/teacher/students"
          class="flex items-center gap-3 p-4 border border-border-light rounded-xl no-underline text-ink text-sm font-medium transition-all duration-200 hover:bg-primary/0.25 hover:border-primary hover:shadow-card">
          <div class="w-10 h-10 rounded-full bg-info/10 text-info flex items-center justify-center">
            <Icons name="mdi-account-group" />
          </div>
          <span>View Students</span>
        </router-link>
        <router-link to="/teacher/courses"
          class="flex items-center gap-3 p-4 border border-border-light rounded-xl no-underline text-ink text-sm font-medium transition-all duration-200 hover:bg-primary/0.25 hover:border-primary hover:shadow-card">
          <div class="w-10 h-10 rounded-full bg-sage/12 text-[#5e6e5f] flex items-center justify-center">
            <Icons name="mdi-book-open-variant" />
          </div>
          <span>My Classes</span>
        </router-link>
      </div>
    </div>
  </div>
</template>
