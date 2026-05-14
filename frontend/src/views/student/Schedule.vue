<script setup>
import { ref, onMounted, computed } from 'vue'
import { getMyEnrollments } from '../../services/api.js'
import { useAuthStore } from '../../stores/auth'
import Icons from '../../components/icon/Icons.vue'

const authStore = useAuthStore()
const loading = ref(true)
const enrollments = ref([])

const fetchSchedule = async () => {
  if (!authStore.user?.user_id) return
  loading.value = true
  try {
    const enrRes = await getMyEnrollments()
    enrollments.value = enrRes.data.enrollments || []
  } catch (error) {
    // If no student profile, enrollments will stay empty
    console.warn('Could not load schedule:', error.response?.data?.detail || error.message)
  } finally {
    loading.value = false
  }
}

const dayAccent = {
  Monday: 'bg-primary', Tuesday: 'bg-coral', Wednesday: 'bg-success',
  Thursday: 'bg-info', Friday: 'bg-sage',
}
const dayBorder = {
  Monday: 'border-l-primary', Tuesday: 'border-l-coral', Wednesday: 'border-l-success',
  Thursday: 'border-l-info', Friday: 'border-l-sage',
}
const dayTimeColor = {
  Monday: 'text-primary', Tuesday: 'text-coral', Wednesday: 'text-success',
  Thursday: 'text-info', Friday: 'text-[#5e6e5f]',
}

const schedule = computed(() => {
  const result = { Monday: [], Tuesday: [], Wednesday: [], Thursday: [], Friday: [], Saturday: [], Sunday: [] }
  enrollments.value.forEach(enr => {
    const sec = enr.section
    if (!sec || !sec.schedule_pattern) return
    const parts = sec.schedule_pattern.split(' ')
    if (parts.length < 2) return
    const dayAbbrs = parts[0].split('/')
    const timeRange = parts.slice(1).join(' ')
    const dayMap = { 'Mon': 'Monday', 'Tue': 'Tuesday', 'Wed': 'Wednesday', 'Thu': 'Thursday', 'Fri': 'Friday', 'Sat': 'Saturday', 'Sun': 'Sunday' }
    dayAbbrs.forEach(abbr => {
      const fullDay = dayMap[abbr]
      if (fullDay) {
        result[fullDay].push({
          time: timeRange,
          course: `${sec.course?.course_code} — ${sec.course?.course_name}`,
          room: sec.room?.room_number || 'TBA',
          instructor: sec.instructor?.username || 'TBA'
        })
      }
    })
  })
  Object.keys(result).forEach(day => result[day].sort((a, b) => a.time.localeCompare(b.time)))
  return result
})

onMounted(fetchSchedule)
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-ink tracking-tight">My Academic Schedule</h1>
      <p class="text-sm text-ink-muted mt-0.5">Your weekly class timetable</p>
    </div>

    <div class="bg-surface border border-border-light rounded-2xl shadow-card animate-fade-in overflow-hidden">
      <!-- Banner -->
      <div class="flex items-center gap-3 px-4 sm:px-6 py-4 sm:py-5 bg-primary text-white">
        <Icons name="mdi-calendar-clock" class="text-xl" />
        <h3 class="text-lg font-semibold m-0">Weekly Class Schedule</h3>
      </div>

      <div class="p-4 sm:p-6">
        <div v-if="loading" class="text-center py-12 text-ink-muted">
          <Icons name="mdi-loading" class="animate-spin w-6 h-6 mb-2" />
          <p>Loading schedule...</p>
        </div>
        <div v-else>
          <div v-for="day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']" :key="day"
            class="mb-8 last:mb-0">
            <!-- Day Header -->
            <div class="flex items-center gap-2.5 mb-3">
              <div class="w-1 h-6 rounded-full" :class="dayAccent[day]"></div>
              <h4 class="text-lg font-bold text-ink m-0 flex-1">{{ day }}</h4>
              <span v-if="schedule[day].length"
                class="px-2.5 py-0.5 rounded-full text-[0.7rem] font-medium bg-sage/15 text-[#5e6e5f]">
                {{ schedule[day].length }} class{{ schedule[day].length > 1 ? 'es' : '' }}
              </span>
            </div>

            <!-- No Classes -->
            <div v-if="schedule[day].length === 0"
              class="ml-4 pl-4 py-3 border-l border-dashed border-border-medium text-ink-muted text-sm italic">
              No classes scheduled
            </div>

            <!-- Class Cards -->
            <div v-else class="flex flex-col gap-2.5 ml-2">
              <div v-for="cls in schedule[day]" :key="cls.course + cls.time"
                class="flex flex-col sm:flex-row gap-2 sm:gap-4 p-3 sm:p-4 rounded-xl border border-border-light border-l-4 bg-surface hover:shadow-card hover:bg-page transition-all duration-200"
                :class="dayBorder[day]">
                <div class="sm:min-w-35 flex items-center gap-1.5 text-sm font-semibold" :class="dayTimeColor[day]">
                  <Icons name="mdi-clock-outline" class="text-base" />
                  {{ cls.time }}
                </div>
                <div class="flex-1">
                  <p class="font-semibold text-sm text-ink m-0 mb-1.5">{{ cls.course }}</p>
                  <div class="flex gap-4">
                    <span class="flex items-center gap-1.5 text-xs text-ink-muted">
                      <Icons name="mdi-door-open" class="text-sm text-sage" /> {{ cls.room }}
                    </span>
                    <span class="flex items-center gap-1.5 text-xs text-ink-muted">
                      <Icons name="mdi-account-tie" class="text-sm text-sage" /> {{ cls.instructor }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
