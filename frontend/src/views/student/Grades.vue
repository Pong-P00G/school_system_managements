<script setup>
import { ref, onMounted, computed } from 'vue'
import { getMyEnrollments, getMyStudentProfile } from '../../services/api.js'
import { useAuthStore } from '../../stores/auth'
import Icons from '../../components/icon/Icons.vue'

const authStore = useAuthStore()
const loading = ref(true)
const studentInfo = ref(null)
const enrollments = ref([])

const fetchGrades = async () => {
  if (!authStore.user?.user_id) return
  loading.value = true
  try {
    const [enrRes, stdRes] = await Promise.allSettled([
      getMyEnrollments(),
      getMyStudentProfile()
    ])
    if (enrRes.status === 'fulfilled') {
      enrollments.value = enrRes.value.data.enrollments || []
    }
    if (stdRes.status === 'fulfilled') {
      studentInfo.value = stdRes.value.data
    }
  } catch (error) {
    console.error('Error fetching grades:', error)
  } finally {
    loading.value = false
  }
}

const gpaSummary = computed(() => ({
  cumulative: studentInfo.value?.cumulative_gpa || '0.00',
  totalCredits: studentInfo.value?.total_credits_earned || 0,
  semesterGPA: studentInfo.value?.gpa || '0.00',
  semesterCredits: enrollments.value.reduce((total, enr) => total + (enr.section?.course?.credits || 0), 0)
}))

const completedEnrollments = computed(() =>
  enrollments.value.filter(enr => enr.enrollment_status === 'completed' || enr.grade)
)

const gradeColor = (grade) => {
  if (!grade) return 'text-ink-muted'
  if (['A', 'A+', 'A-'].includes(grade)) return 'text-success'
  if (['B', 'B+', 'B-'].includes(grade)) return 'text-info'
  if (['C', 'C+', 'C-'].includes(grade)) return 'text-warning'
  return 'text-error'
}

onMounted(fetchGrades)
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-ink tracking-tight">Academic Records</h1>
      <p class="text-sm text-ink-muted mt-0.5">Your GPA summary and course grades</p>
    </div>

    <!-- GPA Summary Cards -->
    <div v-if="!loading" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        class="bg-surface border border-border-light rounded-2xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 relative overflow-hidden animate-fade-in delay-1">
        <div class="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-primary"></div>
        <div class="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center text-lg mb-3">
          <Icons name="mdi-school" />
        </div>
        <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Cumulative GPA</p>
        <p class="text-3xl font-bold text-primary">{{ gpaSummary.cumulative }}</p>
      </div>
      <div
        class="bg-surface border border-border-light rounded-2xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 relative overflow-hidden animate-fade-in delay-2">
        <div class="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-info"></div>
        <div class="w-10 h-10 rounded-full bg-info/10 text-info flex items-center justify-center text-lg mb-3">
          <Icons name="mdi-certificate" />
        </div>
        <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Credits Earned</p>
        <p class="text-3xl font-bold text-ink">{{ gpaSummary.totalCredits }}</p>
      </div>
      <div
        class="bg-surface border border-border-light rounded-2xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 relative overflow-hidden animate-fade-in delay-3">
        <div class="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-sage"></div>
        <div class="w-10 h-10 rounded-full bg-sage/12 text-[#5e6e5f] flex items-center justify-center text-lg mb-3">
          <Icons name="mdi-chart-line" />
        </div>
        <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Term GPA</p>
        <p class="text-3xl font-bold text-ink">{{ gpaSummary.semesterGPA }}</p>
      </div>
      <div
        class="bg-surface border border-border-light rounded-2xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 relative overflow-hidden animate-fade-in delay-4">
        <div class="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-coral"></div>
        <div class="w-10 h-10 rounded-full bg-coral/12 text-coral flex items-center justify-center text-lg mb-3">
          <Icons name="mdi-book-open-variant" />
        </div>
        <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Term Credits</p>
        <p class="text-3xl font-bold text-ink">{{ gpaSummary.semesterCredits }}</p>
      </div>
    </div>

    <!-- Grades Table -->
    <div class="bg-surface border border-border-light rounded-2xl shadow-card animate-fade-in delay-3">
      <div class="flex items-center gap-2 px-6 py-4 border-b border-border-light">
        <div class="w-7 h-7 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm">
          <Icons name="mdi-format-list-bulleted" />
        </div>
        <h3 class="text-base font-semibold text-ink">Course Grades</h3>
      </div>

      <div v-if="loading" class="text-center py-10 text-ink-muted">
        <Icons name="mdi-loading" class="animate-spin w-6 h-6 mb-2" />
        <p>Loading academic records...</p>
      </div>
      <div v-else-if="completedEnrollments.length === 0" class="text-center py-10 text-ink-muted">
        <Icons name="mdi-file-document-outline" class="w-10 h-10 mb-2" />
        <p>No grade records found.</p>
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full border-collapse" style="min-width: 600px;">
          <thead class="bg-page">
            <tr>
              <th
                class="px-6 py-3.5 text-left text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Course</th>
              <th
                class="px-6 py-3.5 text-left text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Credits</th>
              <th
                class="px-6 py-3.5 text-left text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Grade</th>
              <th
                class="px-6 py-3.5 text-left text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Points</th>
              <th
                class="px-6 py-3.5 text-left text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Term</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="enr in completedEnrollments" :key="enr.enrollment_id"
              class="border-b border-border-light last:border-b-0 hover:bg-primary/0.25 transition-colors">
              <td class="px-6 py-3.5 text-sm">
                <p class="font-medium text-ink">{{ enr.section?.course?.course_code }}</p>
                <p class="text-xs text-ink-muted">{{ enr.section?.course?.course_name }}</p>
              </td>
              <td class="px-6 py-3.5 text-sm text-ink">{{ enr.section?.course?.credits }}</td>
              <td class="px-6 py-3.5">
                <span class="font-bold text-base" :class="gradeColor(enr.grade)">{{ enr.grade || 'IP' }}</span>
              </td>
              <td class="px-6 py-3.5 text-sm text-ink">{{ enr.grade_points || '—' }}</td>
              <td class="px-6 py-3.5 text-sm text-ink-muted">{{ enr.section?.term?.term_name }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
