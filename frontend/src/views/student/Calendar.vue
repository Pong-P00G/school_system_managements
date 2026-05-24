<script setup>
import { ref, computed, onMounted } from 'vue'
import { getMyEnrollments, getMyAssignments } from '../../services/api'
import Icons from '../../components/icon/Icons.vue'

const loading = ref(true)
const assignments = ref([])
const enrollments = ref([])

async function fetchData() {
  loading.value = true
  try {
    const [asnRes, enrRes] = await Promise.allSettled([getMyAssignments(), getMyEnrollments()])
    if (asnRes.status === 'fulfilled') assignments.value = asnRes.value.data.assignments || asnRes.value.data || []
    if (enrRes.status === 'fulfilled') enrollments.value = enrRes.value.data.enrollments || []
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const today = new Date().toISOString().slice(0, 10)

const deadlines = computed(() => {
  const items = []
  // Assignments with due dates
  assignments.value.forEach(a => {
    if (a.due_date) {
      items.push({
        id: 'a-' + a.assignment_id,
        title: a.assignment_name,
        course: a.course_name || a.section?.course?.course_name || '',
        date: a.due_date.slice(0, 10),
        type: 'assignment',
        icon: 'mdi-file-document-outline',
      })
    }
  })
  // Section end dates
  enrollments.value.forEach(e => {
    if (e.section?.end_date) {
      items.push({
        id: 'e-' + e.enrollment_id,
        title: 'Course Ends',
        course: e.section?.course?.course_code + ' — ' + e.section?.course?.course_name,
        date: e.section.end_date,
        type: 'term',
        icon: 'mdi-calendar-end',
      })
    }
  })
  return items.sort((a, b) => a.date.localeCompare(b.date))
})

const upcomingDeadlines = computed(() => deadlines.value.filter(d => d.date >= today))
const pastDeadlines = computed(() => deadlines.value.filter(d => d.date < today).reverse())

const daysUntil = (date) => {
  const diff = Math.ceil((new Date(date) - new Date(today)) / (1000 * 60 * 60 * 24))
  if (diff === 0) return 'Today'
  if (diff === 1) return 'Tomorrow'
  if (diff < 0) return `${Math.abs(diff)}d ago`
  return `In ${diff} days`
}

const urgencyClass = (date) => {
  const diff = Math.ceil((new Date(date) - new Date(today)) / (1000 * 60 * 60 * 24))
  if (diff <= 0) return 'bg-error/12 text-error'
  if (diff <= 3) return 'bg-warning/12 text-[#b45309]'
  return 'bg-primary/10 text-primary'
}

onMounted(fetchData)
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-ink tracking-tight">Academic Calendar</h1>
      <p class="text-sm text-ink-muted mt-0.5">Upcoming deadlines and important dates</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-ink-muted">
      <Icons name="mdi-loading" class="animate-spin w-8 h-8 mb-2" /><p>Loading calendar...</p>
    </div>

    <template v-else>
      <!-- Summary -->
      <div class="flex flex-wrap gap-4 px-1">
        <div class="flex items-center gap-2 text-sm text-ink-muted">
          <Icons name="mdi-calendar-clock" class="text-warning" />
          <span><strong class="text-ink">{{ upcomingDeadlines.length }}</strong> Upcoming</span>
        </div>
        <div class="flex items-center gap-2 text-sm text-ink-muted">
          <Icons name="mdi-calendar-check" class="text-success" />
          <span><strong class="text-ink">{{ pastDeadlines.length }}</strong> Past</span>
        </div>
      </div>

      <!-- Upcoming -->
      <div class="bg-surface border border-border-light rounded-2xl shadow-card">
        <div class="flex items-center gap-2 px-6 py-4 border-b border-border-light">
          <Icons name="mdi-calendar-clock" class="text-lg text-warning" />
          <h3 class="text-base font-semibold text-ink">Upcoming Deadlines</h3>
        </div>
        <div v-if="upcomingDeadlines.length === 0" class="text-center py-10 text-ink-muted">
          <Icons name="mdi-party-popper" class="w-10 h-10 mb-2" />
          <p>No upcoming deadlines! 🎉</p>
        </div>
        <div v-else>
          <div v-for="item in upcomingDeadlines" :key="item.id"
            class="flex items-center gap-3 px-4 sm:px-6 py-3.5 border-b border-border-light last:border-b-0 hover:bg-page transition-colors">
            <div class="w-9 h-9 rounded-full flex items-center justify-center text-base shrink-0"
              :class="item.type === 'assignment' ? 'bg-coral/12 text-coral' : 'bg-info/10 text-info'">
              <Icons :name="item.icon" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-ink truncate">{{ item.title }}</p>
              <p class="text-xs text-ink-muted truncate">{{ item.course }}</p>
            </div>
            <div class="text-right shrink-0">
              <span class="px-2.5 py-1 rounded-full text-[0.7rem] font-medium" :class="urgencyClass(item.date)">
                {{ daysUntil(item.date) }}
              </span>
              <p class="text-xs text-ink-muted mt-1">{{ new Date(item.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Past -->
      <div v-if="pastDeadlines.length > 0" class="bg-surface border border-border-light rounded-2xl shadow-card">
        <div class="flex items-center gap-2 px-6 py-4 border-b border-border-light">
          <Icons name="mdi-history" class="text-lg text-ink-muted" />
          <h3 class="text-base font-semibold text-ink">Past Deadlines</h3>
        </div>
        <div>
          <div v-for="item in pastDeadlines.slice(0, 10)" :key="item.id"
            class="flex items-center gap-3 px-4 sm:px-6 py-3 border-b border-border-light last:border-b-0 opacity-60">
            <div class="w-8 h-8 rounded-full bg-border-light text-ink-muted flex items-center justify-center text-sm shrink-0">
              <Icons :name="item.icon" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-ink-secondary truncate">{{ item.title }}</p>
              <p class="text-xs text-ink-muted truncate">{{ item.course }}</p>
            </div>
            <span class="text-xs text-ink-muted">{{ new Date(item.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
