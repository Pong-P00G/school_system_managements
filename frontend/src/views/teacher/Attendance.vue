<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getSectionAttendance,
  getSectionEnrollments,
  recordBulkAttendance,
  getSections,
  getFacultySections,
} from '../../services/api.js'
import { useAuthStore } from '../../stores/auth.js'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const saving = ref(false)
const sections = ref([])
const selectedSectionId = ref(route.query.section_id || '')
const selectedDate = ref(new Date().toISOString().split('T')[0])
const attendanceRecords = ref([])
const error = ref('')
const success = ref('')

const sectionOptions = computed(() =>
  sections.value.map((s) => ({
    value: s.section_id,
    label: `${s.course?.course_code || 'N/A'} - ${s.course?.course_name || 'Section'} (Sec ${s.section_number})`,
  }))
)

const statuses = ['present', 'absent', 'late', 'excused', 'holiday']

const statusColors = {
  present: 'bg-emerald-100 text-emerald-800 border-emerald-300',
  absent: 'bg-red-100 text-red-800 border-red-300',
  late: 'bg-amber-100 text-amber-800 border-amber-300',
  excused: 'bg-blue-100 text-blue-800 border-blue-300',
  holiday: 'bg-purple-100 text-purple-800 border-purple-300',
}

const presentCount = computed(() =>
  attendanceRecords.value.filter((r) => r.attendance_status === 'present').length
)
const absentCount = computed(() =>
  attendanceRecords.value.filter((r) => r.attendance_status === 'absent').length
)
const lateCount = computed(() =>
  attendanceRecords.value.filter((r) => r.attendance_status === 'late').length
)
const excusedCount = computed(() =>
  attendanceRecords.value.filter((r) => r.attendance_status === 'excused').length
)

async function loadSections() {
  try {
    const isAdmin = authStore.userRole === 'admin' || authStore.userRole === 'super-admin'
    const res = isAdmin
      ? await getSections(0, 200)
      : await getFacultySections('me')
    sections.value = res.data.sections || res.data
  } catch {
    error.value = 'Failed to load sections'
  }
}

async function loadAttendance() {
  if (!selectedSectionId.value || !selectedDate.value) return
  loading.value = true
  error.value = ''
  try {
    const res = await getSectionAttendance(selectedSectionId.value, {
      class_date: selectedDate.value,
      per_page: 200,
    })
    // If no records exist yet, show students from section enrollments as unmarked
    if (res.data.attendance_records?.length > 0) {
      attendanceRecords.value = res.data.attendance_records.map((r) => ({
        ...r,
        _status: r.attendance_status,
      }))
    } else {
      // Load enrollments to show all students
      const enrollRes = await getSectionEnrollments(selectedSectionId.value)
      attendanceRecords.value = (enrollRes.data?.enrollments || []).map((e) => ({
        student_id: e.student_id,
        student_name: e.student?.user?.full_name || e.student?.user?.username || 'Unknown',
        student_number: e.student?.student_number || '',
        attendance_id: null,
        class_date: selectedDate.value,
        attendance_status: '',
        _status: '',
        arrival_time: null,
        notes: null,
      }))
    }
  } catch (e) {
    error.value = 'Failed to load attendance records'
    console.error(e)
  } finally {
    loading.value = false
  }
}

function setAllStatus(status) {
  attendanceRecords.value.forEach((r) => {
    r._status = status
  })
}

function toggleStatus(record) {
  const statusOrder = ['present', 'absent', 'late', 'excused']
  const idx = statusOrder.indexOf(record._status)
  record._status = statusOrder[(idx + 1) % statusOrder.length]
}

async function saveAttendance() {
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    const records = attendanceRecords.value
      .filter((r) => r._status)
      .map((r) => ({
        section_id: Number(selectedSectionId.value),
        student_id: r.student_id,
        class_date: selectedDate.value,
        attendance_status: r._status,
        arrival_time: r.arrival_time || null,
        notes: r.notes || null,
      }))

    if (records.length === 0) {
      error.value = 'No attendance statuses selected'
      saving.value = false
      return
    }

    await recordBulkAttendance(records)
    success.value = `Saved attendance for ${records.length} student(s)`
    await loadAttendance()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to save attendance'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadSections()
  if (selectedSectionId.value) {
    await loadAttendance()
  }
})

watch(selectedSectionId, () => {
  if (selectedSectionId.value) loadAttendance()
})

watch(selectedDate, () => {
  if (selectedSectionId.value) loadAttendance()
})
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <div class="mb-6">
      <div class="flex items-center justify-between mb-2">
        <h1 class="text-2xl font-bold text-ink">Attendance Management</h1>
      </div>
      <p class="text-ink-muted text-sm">Record and manage student attendance for your course sections.</p>
    </div>

    <!-- Filters -->
    <div class="bg-surface rounded-xl shadow-sm border border-border p-5 mb-6">
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label class="block text-xs font-semibold text-ink-muted uppercase tracking-wide mb-1.5">Section</label>
          <select
            v-model="selectedSectionId"
            class="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
          >
            <option value="">Select a section...</option>
            <option v-for="opt in sectionOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-semibold text-ink-muted uppercase tracking-wide mb-1.5">Class Date</label>
          <input
            v-model="selectedDate"
            type="date"
            class="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
          />
        </div>
        <div class="flex items-end gap-2">
          <button
            @click="loadAttendance"
            :disabled="!selectedSectionId || loading"
            class="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {{ loading ? 'Loading...' : 'Refresh' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div v-if="attendanceRecords.length > 0" class="flex flex-wrap items-center gap-2 mb-4">
      <span class="text-xs font-semibold text-ink-muted uppercase mr-1">Quick Fill:</span>
      <button
        v-for="status in statuses"
        :key="status"
        @click="setAllStatus(status)"
        class="px-3 py-1 rounded-lg text-xs font-medium border transition-colors"
        :class="statusColors[status] || 'bg-gray-100 text-gray-700 border-gray-300'"
      >
        {{ status.charAt(0).toUpperCase() + status.slice(1) }}
      </button>
    </div>

    <!-- Summary Stats -->
    <div v-if="attendanceRecords.length > 0" class="flex flex-wrap gap-4 mb-4">
      <div class="px-3 py-1.5 rounded-lg bg-gray-50 border border-border text-sm">
        <span class="text-ink-muted">Present:</span>
        <span class="font-semibold text-emerald-700 ml-1">{{ presentCount }}</span>
      </div>
      <div class="px-3 py-1.5 rounded-lg bg-gray-50 border border-border text-sm">
        <span class="text-ink-muted">Absent:</span>
        <span class="font-semibold text-red-700 ml-1">{{ absentCount }}</span>
      </div>
      <div class="px-3 py-1.5 rounded-lg bg-gray-50 border border-border text-sm">
        <span class="text-ink-muted">Late:</span>
        <span class="font-semibold text-amber-700 ml-1">{{ lateCount }}</span>
      </div>
      <div class="px-3 py-1.5 rounded-lg bg-gray-50 border border-border text-sm">
        <span class="text-ink-muted">Excused:</span>
        <span class="font-semibold text-blue-700 ml-1">{{ excusedCount }}</span>
      </div>
    </div>

    <!-- Status Messages -->
    <div v-if="error" class="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
      {{ error }}
    </div>
    <div v-if="success" class="mb-4 px-4 py-3 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-700">
      {{ success }}
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin mb-3"></div>
      <p class="text-ink-muted text-sm">Loading attendance records...</p>
    </div>

    <!-- Attendance Table -->
    <div v-else-if="attendanceRecords.length > 0" class="bg-surface rounded-xl shadow-sm border border-border overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-gray-50 border-b border-border">
              <th class="text-left px-4 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide w-12">
                #
              </th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide">
                Student
              </th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide">
                ID
              </th>
              <th class="text-center px-4 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide w-40">
                Status
              </th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide w-24">
                Arrival
              </th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide">
                Notes
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(record, idx) in attendanceRecords"
              :key="record.student_id"
              class="border-b border-border last:border-b-0 hover:bg-gray-50/50 transition-colors"
            >
              <td class="px-4 py-3 text-sm text-ink-muted">{{ idx + 1 }}</td>
              <td class="px-4 py-3">
                <span class="text-sm font-medium text-ink">{{ record.student_name }}</span>
              </td>
              <td class="px-4 py-3 text-sm text-ink-muted">{{ record.student_number || '—' }}</td>
              <td class="px-4 py-3 text-center">
                <div class="flex items-center justify-center gap-1">
                  <button
                    v-for="status in statuses"
                    :key="status"
                    @click="record._status = status"
                    class="px-2 py-0.5 rounded text-[0.7rem] font-medium border transition-all"
                    :class="record._status === status
                      ? (statusColors[status] || 'bg-gray-200 text-gray-800 border-gray-400')
                      : 'bg-transparent text-gray-400 border-gray-200 hover:border-gray-300'"
                  >
                    {{ status === 'present' ? 'P' : status === 'absent' ? 'A' : status === 'late' ? 'L' : status === 'excused' ? 'E' : 'H' }}
                  </button>
                </div>
              </td>
              <td class="px-4 py-3">
                <input
                  v-model="record.arrival_time"
                  type="time"
                  class="w-full rounded border border-border px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-primary/30 focus:border-primary"
                />
              </td>
              <td class="px-4 py-3">
                <input
                  v-model="record.notes"
                  type="text"
                  placeholder="Optional notes..."
                  class="w-full rounded border border-border px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-primary/30 focus:border-primary"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- No Data -->
    <div v-else-if="selectedSectionId" class="text-center py-12 bg-surface rounded-xl shadow-sm border border-border">
      <div class="text-4xl mb-3">📋</div>
      <p class="text-ink-muted text-sm">No students found for this section. Enroll students first.</p>
    </div>

    <!-- Select Prompt -->
    <div v-else class="text-center py-12 bg-surface rounded-xl shadow-sm border border-border">
      <div class="text-4xl mb-3">📊</div>
      <p class="text-ink-muted text-sm">Select a section and date to manage attendance.</p>
    </div>

    <!-- Save Button -->
    <div v-if="attendanceRecords.length > 0" class="mt-6 flex justify-end">
      <button
        @click="saveAttendance"
        :disabled="saving"
        class="px-6 py-2.5 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
      >
        <svg v-if="saving" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
        {{ saving ? 'Saving...' : 'Save Attendance' }}
      </button>
    </div>
  </div>
</template>
