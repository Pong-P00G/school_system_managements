<script setup>
import { ref, computed, onMounted } from 'vue'
import { getMyAttendance } from '../../services/api.js'

const loading = ref(true)
const attendanceRecords = ref([])
const error = ref('')
const filterStatus = ref('')
const filterDate = ref('')

const statusBadgeColors = {
  present: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  absent: 'bg-red-50 text-red-700 border-red-200',
  late: 'bg-amber-50 text-amber-700 border-amber-200',
  excused: 'bg-blue-50 text-blue-700 border-blue-200',
  holiday: 'bg-purple-50 text-purple-700 border-purple-200',
}

const filteredRecords = computed(() => {
  let records = attendanceRecords.value
  if (filterStatus.value) {
    records = records.filter((r) => r.attendance_status === filterStatus.value)
  }
  if (filterDate.value) {
    records = records.filter((r) => r.class_date === filterDate.value)
  }
  return records
})

const stats = computed(() => {
  const total = attendanceRecords.value.length
  if (!total) return { total: 0, present: 0, absent: 0, late: 0, excused: 0, rate: 0 }
  const present = attendanceRecords.value.filter((r) => r.attendance_status === 'present').length
  const absent = attendanceRecords.value.filter((r) => r.attendance_status === 'absent').length
  const late = attendanceRecords.value.filter((r) => r.attendance_status === 'late').length
  const excused = attendanceRecords.value.filter((r) => r.attendance_status === 'excused').length
  return {
    total,
    present,
    absent,
    late,
    excused,
    rate: total > 0 ? Math.round(((present + excused) / total) * 100) : 0,
  }
})

const uniqueDates = computed(() => {
  const dates = [...new Set(attendanceRecords.value.map((r) => r.class_date))]
  return dates.sort().reverse()
})

async function loadAttendance() {
  loading.value = true
  error.value = ''
  try {
    const res = await getMyAttendance({ per_page: 200 })
    attendanceRecords.value = res.data.attendance_records || []
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load attendance records'
  } finally {
    loading.value = false
  }
}

onMounted(loadAttendance)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="bg-primary rounded-2xl p-5 sm:p-8 text-white relative overflow-hidden animate-fade-in">
      <div class="absolute -top-[40%] -right-[10%] w-80 h-80 bg-white/6 rounded-full"></div>
      <div class="relative z-10">
        <p class="text-sm opacity-75 mb-0.5">Overview</p>
        <h1 class="text-2xl font-bold mb-1">My Attendance</h1>
        <p class="text-sm opacity-70">Track your attendance across all enrolled classes.</p>
      </div>
      <div v-if="!loading && attendanceRecords.length > 0" class="relative z-10 mt-5">
        <div class="flex items-center gap-3 mb-3">
          <span class="px-3 py-1 rounded-full text-xs font-medium bg-white/15">{{ stats.total }} Classes</span>
          <span class="px-3 py-1 rounded-full text-xs font-medium bg-white/15">{{ stats.rate }}% Attendance Rate</span>
        </div>
        <div class="w-full h-2 bg-white/20 rounded-full overflow-hidden">
          <div class="h-full rounded-full transition-all duration-500"
            :class="stats.rate >= 80 ? 'bg-emerald-400' : stats.rate >= 60 ? 'bg-amber-400' : 'bg-red-400'"
            :style="{ width: stats.rate + '%' }"></div>
        </div>
      </div>
    </div>

    <!-- Stats Cards -->
    <div v-if="!loading && attendanceRecords.length > 0" class="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
      <div class="bg-surface border border-border-light rounded-2xl p-5 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 relative overflow-hidden animate-fade-in delay-1">
        <div class="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-emerald-500"></div>
        <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Present</p>
        <p class="text-3xl font-bold text-emerald-600">{{ stats.present }}</p>
      </div>
      <div class="bg-surface border border-border-light rounded-2xl p-5 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 relative overflow-hidden animate-fade-in delay-2">
        <div class="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-red-500"></div>
        <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Absent</p>
        <p class="text-3xl font-bold text-red-600">{{ stats.absent }}</p>
      </div>
      <div class="bg-surface border border-border-light rounded-2xl p-5 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 relative overflow-hidden animate-fade-in delay-3">
        <div class="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-amber-500"></div>
        <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Late</p>
        <p class="text-3xl font-bold text-amber-600">{{ stats.late }}</p>
      </div>
      <div class="bg-surface border border-border-light rounded-2xl p-5 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 relative overflow-hidden animate-fade-in delay-4">
        <div class="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-blue-500"></div>
        <p class="text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Excused</p>
        <p class="text-3xl font-bold text-blue-600">{{ stats.excused }}</p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-ink-muted animate-fade-in">
      <div class="inline-block w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin mb-3"></div>
      <p class="text-sm">Loading attendance records...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="bg-surface border border-border-light rounded-2xl shadow-card p-10 text-center animate-fade-in">
      <div class="w-12 h-12 rounded-full bg-red-50 text-red-500 flex items-center justify-center text-xl mx-auto mb-3">⚠️</div>
      <p class="text-red-600 text-sm font-medium">{{ error }}</p>
    </div>

    <!-- Empty -->
    <div v-else-if="attendanceRecords.length === 0" class="bg-surface border border-border-light rounded-2xl shadow-card p-10 text-center animate-fade-in">
      <div class="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xl mx-auto mb-3">📊</div>
      <p class="text-ink-muted text-sm">No attendance records found yet.</p>
    </div>

    <!-- Records -->
    <div v-else class="bg-surface border border-border-light rounded-2xl shadow-card animate-fade-in delay-3">
      <!-- Filters -->
      <div class="flex flex-wrap items-center gap-3 px-6 py-4 border-b border-border-light">
        <div class="flex items-center gap-2">
          <label class="text-xs font-medium text-ink-muted">Status:</label>
          <select
            v-model="filterStatus"
            class="rounded-lg border border-border-light bg-white px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 transition-shadow"
          >
            <option value="">All</option>
            <option value="present">Present</option>
            <option value="absent">Absent</option>
            <option value="late">Late</option>
            <option value="excused">Excused</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <label class="text-xs font-medium text-ink-muted">Date:</label>
          <select
            v-model="filterDate"
            class="rounded-lg border border-border-light bg-white px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 transition-shadow"
          >
            <option value="">All</option>
            <option v-for="d in uniqueDates" :key="d" :value="d">{{ d }}</option>
          </select>
        </div>
        <span class="text-xs text-ink-muted ml-auto">
          {{ filteredRecords.length }} of {{ attendanceRecords.length }} records
        </span>
      </div>

      <!-- Table -->
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-border-light">
              <th class="text-left px-6 py-3 text-xs font-medium text-ink-muted uppercase tracking-wide">Date</th>
              <th class="text-left px-6 py-3 text-xs font-medium text-ink-muted uppercase tracking-wide">Course</th>
              <th class="text-left px-6 py-3 text-xs font-medium text-ink-muted uppercase tracking-wide">Section</th>
              <th class="text-center px-6 py-3 text-xs font-medium text-ink-muted uppercase tracking-wide">Status</th>
              <th class="text-left px-6 py-3 text-xs font-medium text-ink-muted uppercase tracking-wide">Arrival</th>
              <th class="text-left px-6 py-3 text-xs font-medium text-ink-muted uppercase tracking-wide">Notes</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="record in filteredRecords"
              :key="record.attendance_id"
              class="border-b border-border-light last:border-b-0 hover:bg-primary/[0.02] transition-colors"
            >
              <td class="px-6 py-4 text-sm font-medium text-ink whitespace-nowrap">{{ record.class_date }}</td>
              <td class="px-6 py-4">
                <p class="text-sm font-medium text-ink">{{ record.section?.course?.course_code || 'N/A' }}</p>
                <p class="text-xs text-ink-muted mt-0.5">{{ record.section?.course?.course_name || '' }}</p>
              </td>
              <td class="px-6 py-4 text-sm text-ink-muted">Sec {{ record.section?.section_number || 'N/A' }}</td>
              <td class="px-6 py-4 text-center">
                <span
                  class="inline-block px-2.5 py-1 rounded-full text-[0.7rem] font-semibold border"
                  :class="statusBadgeColors[record.attendance_status] || 'bg-gray-100 text-gray-700 border-gray-300'"
                >
                  {{ record.attendance_status ? record.attendance_status.charAt(0).toUpperCase() + record.attendance_status.slice(1).replace('_', ' ') : 'N/A' }}
                </span>
              </td>
              <td class="px-6 py-4 text-sm text-ink-muted">{{ record.arrival_time || '—' }}</td>
              <td class="px-6 py-4 text-sm text-ink-muted max-w-48 truncate">{{ record.notes || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
