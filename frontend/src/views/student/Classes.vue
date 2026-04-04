<script setup>
import { computed, onMounted, ref } from 'vue'
import { getMyEnrollments, getMyStudentProfile } from '../../services/api.js'
import Icons from '../../components/icon/Icons.vue'

const loading = ref(true)
const noStudentProfile = ref(false)
const studentProfile = ref(null)
const enrollments = ref([])

const loadClasses = async () => {
  loading.value = true
  noStudentProfile.value = false
  try {
    const [profileRes, enrollmentsRes] = await Promise.allSettled([
      getMyStudentProfile(),
      getMyEnrollments()
    ])

    if (profileRes.status === 'fulfilled') {
      studentProfile.value = profileRes.value.data
    } else {
      noStudentProfile.value = true
      studentProfile.value = null
      console.warn('Could not load student profile:', profileRes.reason?.response?.data?.detail || profileRes.reason?.message)
    }

    if (enrollmentsRes.status === 'fulfilled') {
      enrollments.value = enrollmentsRes.value.data.enrollments || []
    } else {
      enrollments.value = []
      console.warn('Could not load classes:', enrollmentsRes.reason?.response?.data?.detail || enrollmentsRes.reason?.message)
    }
  } finally {
    loading.value = false
  }
}

const activeClasses = computed(() =>
  enrollments.value.filter(enr => enr.enrollment_status === 'enrolled')
)

const completedClasses = computed(() =>
  enrollments.value.filter(enr => enr.enrollment_status === 'completed')
)

const totalCredits = computed(() =>
  enrollments.value.reduce((sum, enr) => sum + Number(enr.section?.course?.credits || 0), 0)
)

const termLabel = computed(() => {
  const firstWithTerm = enrollments.value.find(enr => enr.section?.term?.term_name)
  return firstWithTerm?.section?.term?.term_name || 'Current Term'
})

const statusClass = (status) => {
  if (status === 'completed') return 'bg-success/12 text-[#047857]'
  if (status === 'withdrawn') return 'bg-coral/12 text-coral'
  return 'bg-primary/10 text-primary'
}

const formatDate = (value) => value ? new Date(value).toLocaleDateString() : 'N/A'
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
      <div>
        <h1 class="text-2xl font-bold text-ink tracking-tight">My Classes</h1>
        <p class="text-sm text-ink-muted mt-0.5">Detailed view of the classes you joined or enrolled in</p>
      </div>
      <router-link to="/student/courses"
        class="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-coral text-white text-sm font-medium no-underline transition-all hover:bg-coral-hover hover:shadow-[0_4px_12px_rgba(224,122,95,0.3)]">
        <Icons name="mdi-plus" />
        Add More Classes
      </router-link>
    </div>

    <div v-if="loading" class="text-center py-12 text-ink-muted">
      <Icons name="mdi-loading" class="animate-spin w-8 h-8 mb-2" />
      <p>Loading your classes...</p>
    </div>

    <div v-else-if="noStudentProfile && enrollments.length === 0"
      class="bg-surface border border-border-light rounded-2xl shadow-card p-8 text-center animate-fade-in">
      <Icons name="mdi-account-alert" class="w-12 h-12 text-coral mb-3" />
      <h3 class="text-lg font-semibold text-ink mb-1">No Student Profile Found</h3>
      <p class="text-sm text-ink-muted">Your account is not linked to a student profile. Please contact the administrator.</p>
    </div>

    <template v-else>
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div class="bg-surface border border-border-light rounded-2xl p-5 shadow-card">
          <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Joined Classes</p>
          <p class="text-3xl font-bold text-ink">{{ enrollments.length }}</p>
        </div>
        <div class="bg-surface border border-border-light rounded-2xl p-5 shadow-card">
          <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Active</p>
          <p class="text-3xl font-bold text-ink">{{ activeClasses.length }}</p>
        </div>
        <div class="bg-surface border border-border-light rounded-2xl p-5 shadow-card">
          <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Completed</p>
          <p class="text-3xl font-bold text-ink">{{ completedClasses.length }}</p>
        </div>
        <div class="bg-surface border border-border-light rounded-2xl p-5 shadow-card">
          <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Credits</p>
          <p class="text-3xl font-bold text-ink">{{ totalCredits }}</p>
        </div>
      </div>

      <div class="bg-surface border border-border-light rounded-2xl shadow-card p-5 sm:p-6 animate-fade-in">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <p class="text-xs uppercase tracking-wider text-ink-muted mb-1">Student</p>
            <h2 class="text-xl font-bold text-ink">
              {{ studentProfile?.user?.personal_info?.first_name || 'Student' }} {{ studentProfile?.user?.personal_info?.last_name || '' }}
            </h2>
            <p class="text-sm text-ink-muted mt-1">
              {{ studentProfile?.student_number }} · {{ studentProfile?.program?.program_name || 'No Program' }}
            </p>
          </div>
          <div class="text-left sm:text-right">
            <p class="text-xs uppercase tracking-wider text-ink-muted mb-1">Academic Term</p>
            <p class="text-sm font-semibold text-ink">{{ termLabel }}</p>
          </div>
        </div>
      </div>

      <div class="bg-surface border border-border-light rounded-2xl shadow-card animate-fade-in overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
          <h3 class="text-base font-semibold text-ink">Class Details</h3>
          <span class="px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">{{ enrollments.length }}
            classes</span>
        </div>

        <div v-if="enrollments.length === 0" class="text-center py-12 text-ink-muted">
          <Icons name="mdi-book-off-outline" class="w-10 h-10 mb-2" />
          <p>You have not joined any classes yet.</p>
        </div>

        <div v-else class="p-4 sm:p-6 grid gap-4">
          <div v-for="enr in enrollments" :key="enr.enrollment_id"
            class="rounded-2xl border border-border-light bg-page/60 p-5 hover:shadow-card transition-all">
            <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
              <div class="flex-1">
                <div class="flex flex-wrap items-center gap-2 mb-2">
                  <span
                    class="px-2 py-0.5 rounded text-[0.65rem] font-bold uppercase tracking-wider bg-primary/10 text-primary">
                    {{ enr.section?.course?.course_code || 'Course' }}
                  </span>
                  <span class="text-xs text-ink-muted">{{ enr.section?.term?.term_name || 'Term N/A' }}</span>
                </div>
                <h3 class="text-lg font-semibold text-ink">{{ enr.section?.course?.course_name || 'Course Name N/A' }}</h3>
                <div class="mt-3 grid sm:grid-cols-2 xl:grid-cols-4 gap-3 text-sm">
                  <div class="flex items-center gap-2 text-ink-muted">
                    <Icons name="mdi-google-classroom" class="text-primary" />
                    <span>Section {{ enr.section?.section_number || 'N/A' }}</span>
                  </div>
                  <div class="flex items-center gap-2 text-ink-muted">
                    <Icons name="mdi-clock-outline" class="text-primary" />
                    <span>{{ enr.section?.schedule_pattern || 'Schedule TBA' }}</span>
                  </div>
                  <div class="flex items-center gap-2 text-ink-muted">
                    <Icons name="mdi-door-open" class="text-primary" />
                    <span>{{ enr.section?.room?.room_number || 'Room TBA' }}</span>
                  </div>
                  <div class="flex items-center gap-2 text-ink-muted">
                    <Icons name="mdi-star-outline" class="text-primary" />
                    <span>{{ enr.section?.course?.credits || 0 }} credits</span>
                  </div>
                </div>
              </div>

              <div class="lg:min-w-52">
                <div class="flex lg:justify-end">
                  <span class="px-3 py-1 rounded-full text-xs font-medium" :class="statusClass(enr.enrollment_status)">
                    {{ enr.enrollment_status }}
                  </span>
                </div>
                <div class="mt-3 space-y-2 text-sm">
                  <div class="flex justify-between gap-4">
                    <span class="text-ink-muted">Enrolled On</span>
                    <span class="font-medium text-ink">{{ formatDate(enr.enrollment_date) }}</span>
                  </div>
                  <div class="flex justify-between gap-4">
                    <span class="text-ink-muted">Midterm</span>
                    <span class="font-medium text-ink">{{ enr.midterm_grade || '-' }}</span>
                  </div>
                  <div class="flex justify-between gap-4">
                    <span class="text-ink-muted">Final</span>
                    <span class="font-medium text-ink">{{ enr.final_grade || enr.grade || '-' }}</span>
                  </div>
                  <div class="flex justify-between gap-4">
                    <span class="text-ink-muted">Attendance</span>
                    <span class="font-medium text-ink">
                      {{ enr.attendance_percentage != null ? `${enr.attendance_percentage}%` : 'N/A' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
