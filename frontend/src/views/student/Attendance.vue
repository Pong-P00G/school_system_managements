<script setup>
import { ref, computed, onMounted } from 'vue'
import { getMyAttendance } from '../../services/api.js'

const loading = ref(true)
const attendanceRecords = ref([])
const error = ref('')
const filterStatus = ref('')
const filterDate = ref('')

const statusColors = {
  present: 'bg-emerald-100 text-emerald-800 border-emerald-300',
  absent: 'bg-red-100 text-red-800 border-red-300',
  late: 'bg-amber-100 text-amber-800 border-amber-300',
  excused: 'bg-blue-100 text-blue-800 border-blue-300',
  holiday: 'bg-purple-100 text-purple-800 border-purple-300',
}

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
    const res = await getMyAttendance({ per_page: 500 })
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
  <div class="max-w-5xl mx-auto">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-ink">My Attendance</h1>
      <p class="text-ink-muted text-sm mt-1">View your attendance records across all enrolled classes.</p>
    </div>

    <!-- Stats Cards -->
    <div v-if="!loading && attendanceRecords.length > 0" class="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
      <div class="bg-surface rounded-xl shadow-sm border border-border p-4 text-center">
        <div class="text-2xl font-bold text-ink">{{ stats.total }}</div>
        <div class="text-[0.7rem] text-ink-muted uppercase tracking-wide font-semibold mt-1">Total</div>
      </div>
      <div class="bg-surface rounded-xl shadow-sm border border-border p-4 text-center">
        <div class="text-2xl font-bold text-emerald-600">{{ stats.present }}</div>
        <div class="text-[0.7rem] text-ink-muted uppercase tracking-wide font-semibold mt-1">Present</div>
      </div>
      <div class="bg-surface rounded-xl shadow-sm border border-border p-4 text-center">
        <div class="text-2xl font-bold text-red-600">{{ stats.absent }}</div>
        <div class="text-[0.7rem] text-ink-muted uppercase tracking-wide font-semibold mt-1">Absent</div>
      </div>
      <div class="bg-surface rounded-xl shadow-sm border border-border p-4 text-center">
        <div class="text-2xl font-bold text-amber-600">{{ stats.late }}</div>
        <div class="text-[0.7rem] text-ink-muted uppercase tracking-wide font-semibold mt-1">Late</div>
      </div>
      <div class="bg-surface rounded-xl shadow-sm border border-border p-4 text-center">
        <div class="text-2xl font-bold text-blue-600">{{ stats.rate }}%</div>
        <div class="text-[0.7rem] text-ink-muted uppercase tracking-wide font-semibold mt-1">Attendance Rate</div>
      </div>
    </div>

    <!-- Filters -->
    <div v-if="attendanceRecords.length > 0" class="bg-surface rounded-xl shadow-sm border border-border p-4 mb-4">
      <div class="flex flex-wrap items-center gap-3">
        <div class="flex items-center gap-2">
          <label class="text-xs font-semibold text-ink-muted">Status:</label>
          <select
            v-model="filterStatus"
            class="rounded-lg border border-border bg-white px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary/30"
          >
            <option value="">All</option>
            <option value="present">Present</option>
            <option value="absent">Absent</option>
            <option value="late">Late</option>
            <option value="excused">Excused</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <label class="text-xs font-semibold text-ink-muted">Date:</label>
          <select
            v-model="filterDate"
            class="rounded-lg border border-border bg-white px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary/30"
          >
            <option value="">All</option>
            <option v-for="d in uniqueDates" :key="d" :value="d">{{ d }}</option>
          </select>
        </div>
        <span class="text-xs text-ink-muted ml-auto">
          Showing {{ filteredRecords.length }} of {{ attendanceRecords.length }} records
        </span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-16">
      <div class="inline-block w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin mb-3"></div>
      <p class="text-ink-muted text-sm">Loading attendance records...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="bg-surface rounded-xl shadow-sm border border-border p-8 text-center">
      <div class="text-4xl mb-3">⚠️</div>
      <p class="text-red-600 text-sm">{{ error }}</p>
    </div>

    <!-- Empty -->
    <div v-else-if="attendanceRecords.length === 0" class="bg-surface rounded-xl shadow-sm border border-border p-8 text-center">
      <div class="text-4xl mb-3">📊</div>
      <p class="text-ink-muted text-sm">No attendance records found yet.</p>
    </div>

    <!-- Attendance Table -->
    <div v-else class="bg-surface rounded-xl shadow-sm border border-border overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-gray-50 border-b border-border">
              <th class="text-left px-4 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide">Date</th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide">Course</th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide">Section</th>
              <th class="text-center px-4 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide">Status</th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide">Arrival</th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide">Notes</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="record in filteredRecords"
              :key="record.attendance_id"
              class="border-b border-border last:border-b-0 hover:bg-gray-50/50 transition-colors"
            >
              <td class="px-4 py-3 text-sm font-medium text-ink">{{ record.class_date }}</td>
              <td class="px-4 py-3">
                <span class="text-sm text-ink">
                  {{ record.section?.course?.course_code || 'N/A' }} -
                  {{ record.section?.course?.course_name || '' }}
                </span>
              </td>
              <td class="px-4 py-3 text-sm text-ink-muted">Sec {{ record.section?.section_number || 'N/A' }}</td>
              <td class="px-4 py-3 text-center">
                <span
                  class="inline-block px-2.5 py-0.5 rounded-full text-[0.7rem] font-semibold border"
                  :class="statusBadgeColors[record.attendance_status] || 'bg-gray-100 text-gray-700 border-gray-300'"
                >
                  {{ record.attendance_status ? record.attendance_status.charAt(0).toUpperCase() + record.attendance_status.slice(1).replace('_', ' ') : 'N/A' }}
                </span>
              </td>
              <td class="px-4 py-3 text-sm text-ink-muted">{{ record.arrival_time || '—' }}</td>
              <td class="px-4 py-3 text-sm text-ink-muted max-w-50 truncate">{{ record.notes || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
