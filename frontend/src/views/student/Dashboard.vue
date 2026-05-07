<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { getMyStudentProfile, getMyEnrollments } from '../../services/api.js'
import Icons from '../../components/icon/Icons.vue'

const authStore = useAuthStore()
const loading = ref(true)
const studentInfo = ref(null)
const enrollments = ref([])
const account = ref(null)

const studentName = computed(() => studentInfo.value?.first_name ? `${studentInfo.value.first_name} ${studentInfo.value.last_name}` : 'Student')
const studentProgram = computed(() => studentInfo.value?.program?.program_name || 'N/A')
const studentGPA = computed(() => studentInfo.value?.gpa || 'N/A')
const enrolledCredits = computed(() => enrollments.value.reduce((total, enr) => total + (enr.section?.course?.credits || 0), 0))
const totalClasses = computed(() => enrollments.value.length)

const upcomingAssignments = ref([
  { name: 'Data Structures Project', due: '2025-02-20', course: 'Data Structures' },
  { name: 'Database Design', due: '2025-02-22', course: 'Database Systems' }
])

onMounted(async () => {
  if (!authStore.user?.user_id) { loading.value = false; return }
  loading.value = true
  try {
    // Use the new /me endpoints that resolve student ID from the auth token
    const [studentRes, enrollmentsRes] = await Promise.allSettled([
      getMyStudentProfile(),
      getMyEnrollments()
    ])

    if (studentRes.status === 'fulfilled') {
      studentInfo.value = studentRes.value.data
      // The profile endpoint includes account info in the 'account' field if loaded
      if (studentRes.value.data.account) {
        account.value = studentRes.value.data.account
      }
    }

    if (enrollmentsRes.status === 'fulfilled') {
      enrollments.value = enrollmentsRes.value.data.enrollments || []
    }
  } catch (error) {
    console.error('Error fetching student data:', error)
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
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center relative z-10 gap-4">
        <div>
          <p class="text-sm opacity-75 m-0 mb-0.5">Welcome back,</p>
          <h1 class="text-2xl font-bold m-0 mb-3">{{ studentName }}</h1>
          <div class="flex gap-2">
            <span class="px-3 py-1 rounded-full text-xs font-medium bg-white/15">{{ studentProgram }}</span>
            <span class="px-3 py-1 rounded-full text-xs font-medium bg-white/15">{{ studentInfo?.year_level || 'Year N/A' }}</span>
          </div>
        </div>
        <div class="text-left sm:text-right">
          <p class="text-[2.5rem] font-bold m-0 leading-none">{{ studentGPA }}</p>
          <p class="text-xs opacity-70 uppercase tracking-widest mt-1.5 m-0">Current GPA</p>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-ink-muted">
      <Icons name="mdi-loading" class="animate-spin w-8 h-8 mb-2" />
      <p>Loading your dashboard...</p>
    </div>

    <!-- Stats -->
    <div v-else class="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4">
      <div
        class="bg-surface border border-border-light rounded-2xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 relative overflow-hidden animate-fade-in delay-1">
        <div class="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-primary"></div>
        <div class="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center text-lg mb-3">
          <Icons name="mdi-book-open-variant" />
        </div>
        <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Enrolled Credits</p>
        <p class="text-3xl font-bold text-ink">{{ enrolledCredits }}</p>
      </div>
      <div
        class="bg-surface border border-border-light rounded-2xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 relative overflow-hidden animate-fade-in delay-2">
        <div class="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-coral"></div>
        <div class="w-10 h-10 rounded-full bg-coral/12 text-coral flex items-center justify-center text-lg mb-3">
          <Icons name="mdi-file-document-outline" />
        </div>
        <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Assignments</p>
        <p class="text-3xl font-bold text-ink">{{ upcomingAssignments.length }}</p>
      </div>
      <div
        class="bg-surface border border-border-light rounded-2xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 relative overflow-hidden animate-fade-in delay-3">
        <div class="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-success"></div>
        <div class="w-10 h-10 rounded-full bg-success/10 text-success flex items-center justify-center text-lg mb-3">
          <Icons name="mdi-account-group" />
        </div>
        <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Active Classes</p>
        <p class="text-3xl font-bold text-ink">{{ totalClasses }}</p>
      </div>
    </div>

    <!-- My Classes -->
    <div v-if="!loading" class="bg-surface border border-border-light rounded-2xl shadow-card animate-fade-in delay-3">
      <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
        <h3 class="text-base font-semibold text-ink">My Classes</h3>
        <router-link to="/student/classes"
          class="text-xs font-medium text-coral no-underline hover:text-coral-hover transition-colors">View All
          →</router-link>
      </div>
      <div>
        <div v-for="enrollment in enrollments.slice(0, 4)" :key="enrollment.enrollment_id"
          class="flex flex-col sm:flex-row sm:items-center justify-between px-4 sm:px-6 py-4 border-b border-border-light last:border-b-0 hover:bg-primary/0.25 transition-colors gap-2 sm:gap-0">
          <div class="flex items-center gap-3">
            <div
              class="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center text-lg shrink-0">
              <Icons name="mdi-book-open-variant" />
            </div>
            <div>
              <p class="font-medium text-sm text-ink">{{ enrollment.section?.course?.course_code }} — {{
                enrollment.section?.course?.course_name }}</p>
              <p class="text-xs text-ink-muted mt-0.5">{{ enrollment.section?.schedule_pattern || 'Schedule TBA' }} · {{
                enrollment.section?.room?.room_number || 'Room TBA' }}</p>
            </div>
          </div>
          <span class="px-3 py-1 rounded-full text-xs font-medium bg-sage/15 text-[#5e6e5f]">{{
            enrollment.enrollment_status }}</span>
        </div>
        <div v-if="enrollments.length === 0" class="text-center py-10 text-ink-muted">
          <Icons name="mdi-book-off-outline" class="w-10 h-10 mb-2" />
          <p>No active classes found.</p>
        </div>
      </div>
    </div>

    <!-- Upcoming Assignments -->
    <div v-if="!loading" class="bg-surface border border-border-light rounded-2xl shadow-card animate-fade-in delay-4">
      <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
        <h3 class="text-base font-semibold text-ink">Upcoming Assignments</h3>
      </div>
      <div>
        <div v-for="assignment in upcomingAssignments" :key="assignment.name"
          class="flex flex-col sm:flex-row sm:items-center justify-between px-4 sm:px-6 py-4 border-b border-border-light last:border-b-0 hover:bg-primary/0.25 transition-colors gap-2 sm:gap-0">
          <div class="flex items-center gap-3">
            <div
              class="w-10 h-10 rounded-full bg-coral/12 text-coral flex items-center justify-center text-lg shrink-0">
              <Icons name="mdi-file-document-outline" />
            </div>
            <div>
              <p class="font-medium text-sm text-ink">{{ assignment.name }}</p>
              <p class="text-xs text-ink-muted mt-0.5">{{ assignment.course }}</p>
            </div>
          </div>
          <span class="px-3 py-1 rounded-full text-xs font-medium bg-warning/12 text-[#b45309]">Due: {{ assignment.due
          }}</span>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div v-if="!loading"
      class="bg-surface border border-border-light rounded-2xl shadow-card p-6 animate-fade-in delay-4">
      <h3 class="text-base font-semibold text-ink mb-4">Quick Actions</h3>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <router-link to="/student/classes"
          class="flex items-center gap-3 p-4 border border-border-light rounded-xl no-underline text-ink text-sm font-medium transition-all duration-200 hover:bg-primary/0.25 hover:border-primary hover:shadow-card">
          <div class="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center">
            <Icons name="mdi-book-open-variant" />
          </div>
          <span>My Classes</span>
        </router-link>
        <router-link to="/student/grades"
          class="flex items-center gap-3 p-4 border border-border-light rounded-xl no-underline text-ink text-sm font-medium transition-all duration-200 hover:bg-primary/0.25 hover:border-primary hover:shadow-card">
          <div class="w-10 h-10 rounded-full bg-success/10 text-success flex items-center justify-center">
            <Icons name="mdi-chart-line" />
          </div>
          <span>View Grades</span>
        </router-link>
        <router-link to="/student/schedule"
          class="flex items-center gap-3 p-4 border border-border-light rounded-xl no-underline text-ink text-sm font-medium transition-all duration-200 hover:bg-primary/0.25 hover:border-primary hover:shadow-card">
          <div class="w-10 h-10 rounded-full bg-sage/12 text-[#5e6e5f] flex items-center justify-center">
            <Icons name="mdi-calendar" />
          </div>
          <span>View Schedule</span>
        </router-link>
      </div>
    </div>
  </div>
</template>
