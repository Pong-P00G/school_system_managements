<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import {
  getSectionAttendance,
  getSectionAttendanceSummary,
  getSectionEnrollments,
  recordBulkAttendance,
  getSections,
  getFacultySections,
  deleteAttendance,
} from '../../services/api.js'
import { useAuthStore } from '../../stores/auth.js'
import { useToast } from '../../composables/useToast.js'

const authStore = useAuthStore()
const toast = useToast()

const loading = ref(false)
const saving = ref(false)
const sections = ref([])
const selectedSectionId = ref('')
const selectedDate = ref(new Date().toISOString().split('T')[0])
const attendanceRecords = ref([])
const summaryData = ref(null)
const showSummary = ref(false)

const statuses = ['present', 'absent', 'late', 'excused']
const statusConfig = {
  present: { label: 'P', color: 'bg-emerald-100 text-emerald-700 border-emerald-300', dot: 'bg-emerald-500' },
  absent: { label: 'A', color: 'bg-red-100 text-red-700 border-red-300', dot: 'bg-red-500' },
  late: { label: 'L', color: 'bg-amber-100 text-amber-700 border-amber-300', dot: 'bg-amber-500' },
  excused: { label: 'E', color: 'bg-blue-100 text-blue-700 border-blue-300', dot: 'bg-blue-500' },
}

const sectionOptions = computed(() =>
  sections.value.map(s => ({
    value: s.section_id,
    label: `${s.course?.course_code || ''} - ${s.course?.course_name || 'Section'} (Sec ${s.section_number})`,
  }))
)

const counts = computed(() => {
  const c = { present: 0, absent: 0, late: 0, excused: 0, unmarked: 0 }
  attendanceRecords.value.forEach(r => {
    if (r._status && c[r._status] !== undefined) c[r._status]++
    else c.unmarked++
  })
  return c
})

const allMarked = computed(() => attendanceRecords.value.every(r => r._status))

async function loadSections() {
  try {
    const isAdmin = ['admin', 'super-admin'].includes(authStore.userRole)
    const res = isAdmin ? await getSections(0, 200) : await getFacultySections('me')
    sections.value = res.data.sections || res.data
  } catch { /* ignore */ }
}

async function loadAttendance() {
  if (!selectedSectionId.value) return
  loading.value = true
  try {
    const res = await getSectionAttendance(selectedSectionId.value, { class_date: selectedDate.value, per_page: 200 })
    if (res.data.attendance_records?.length > 0) {
      attendanceRecords.value = res.data.attendance_records.map(r => ({ ...r, _status: r.attendance_status }))
    } else {
      const enrollRes = await getSectionEnrollments(selectedSectionId.value, null, 0, 200)
      attendanceRecords.value = (enrollRes.data?.enrollments || []).map(e => ({
        student_id: e.student_id,
        student_name: e.student?.user?.username || 'Unknown',
        student_number: e.student?.student_number || '',
        attendance_id: null,
        _status: '',
        arrival_time: null,
        notes: null,
      }))
    }
  } catch {
    toast.error('Failed to load attendance')
  } finally {
    loading.value = false
  }
}

async function loadSummary() {
  if (!selectedSectionId.value) return
  try {
    const res = await getSectionAttendanceSummary(selectedSectionId.value)
    summaryData.value = res.data
    showSummary.value = true
  } catch {
    toast.error('Failed to load summary')
  }
}

function setAllStatus(status) {
  attendanceRecords.value.forEach(r => { r._status = status })
}

async function saveAttendance() {
  const records = attendanceRecords.value
    .filter(r => r._status)
    .map(r => ({
      section_id: Number(selectedSectionId.value),
      student_id: r.student_id,
      class_date: selectedDate.value,
      attendance_status: r._status,
      arrival_time: r.arrival_time || null,
      notes: r.notes || null,
    }))
  if (!records.length) { toast.warning('No statuses selected'); return }
  saving.value = true
  try {
    await recordBulkAttendance(records)
    toast.success(`Saved attendance for ${records.length} student(s)`)
    await loadAttendance()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to save')
  } finally {
    saving.value = false
  }
}

function prevDate() {
  const d = new Date(selectedDate.value)
  d.setDate(d.getDate() - 1)
  selectedDate.value = d.toISOString().split('T')[0]
}
function nextDate() {
  const d = new Date(selectedDate.value)
  d.setDate(d.getDate() + 1)
  const today = new Date().toISOString().split('T')[0]
  const next = d.toISOString().split('T')[0]
  if (next <= today) selectedDate.value = next
}

onMounted(async () => {
  await loadSections()
  if (selectedSectionId.value) await loadAttendance()
})
watch(selectedSectionId, () => { if (selectedSectionId.value) loadAttendance() })
watch(selectedDate, () => { if (selectedSectionId.value) loadAttendance() })
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-[1.75rem] font-bold text-ink tracking-tight">Attendance</h1>
        <p class="text-sm text-ink-muted mt-0.5">Record and manage student attendance</p>
      </div>
      <button v-if="selectedSectionId" @click="loadSummary"
        class="px-4 py-2 bg-primary/10 text-primary rounded-lg text-sm font-medium hover:bg-primary/15 transition-colors">
        View Summary
      </button>
    </div>

    <!-- Section & Date Selector -->
    <div class="bg-surface rounded-xl border border-border-light p-5 mb-5" style="box-shadow: var(--shadow-card)">
      <div class="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-4">
        <div>
          <label class="block text-[0.7rem] font-bold text-ink-muted uppercase tracking-wider mb-1.5">Section</label>
          <select v-model="selectedSectionId"
            class="w-full rounded-lg border-[1.5px] border-border-medium bg-surface px-3 py-2.5 text-sm text-ink font-medium focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all">
            <option value="">Select a section...</option>
            <option v-for="opt in sectionOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
        <div>
          <label class="block text-[0.7rem] font-bold text-ink-muted uppercase tracking-wider mb-1.5">Date</label>
          <div class="flex items-center gap-1">
            <button @click="prevDate" class="p-2.5 rounded-lg border border-border-light hover:bg-page transition-colors">
              <svg class="w-4 h-4 text-ink-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
            </button>
            <input v-model="selectedDate" type="date"
              class="rounded-lg border-[1.5px] border-border-medium bg-surface px-3 py-2.5 text-sm text-ink font-medium focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all" />
            <button @click="nextDate" class="p-2.5 rounded-lg border border-border-light hover:bg-page transition-colors">
              <svg class="w-4 h-4 text-ink-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Fill & Stats Bar -->
    <div v-if="attendanceRecords.length > 0" class="flex flex-wrap items-center justify-between gap-3 mb-4">
      <div class="flex items-center gap-2">
        <span class="text-[0.7rem] font-bold text-ink-muted uppercase tracking-wider">Mark All:</span>
        <button v-for="s in statuses" :key="s" @click="setAllStatus(s)"
          class="px-2.5 py-1 rounded-md text-xs font-semibold border transition-all hover:scale-105"
          :class="statusConfig[s].color">
          {{ s.charAt(0).toUpperCase() + s.slice(1) }}
        </button>
      </div>
      <div class="flex items-center gap-3 text-sm">
        <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-emerald-500"></span><span class="font-semibold">{{ counts.present }}</span></span>
        <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-red-500"></span><span class="font-semibold">{{ counts.absent }}</span></span>
        <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-amber-500"></span><span class="font-semibold">{{ counts.late }}</span></span>
        <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-blue-500"></span><span class="font-semibold">{{ counts.excused }}</span></span>
        <span v-if="counts.unmarked" class="text-ink-muted">{{ counts.unmarked }} unmarked</span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-16">
      <div class="w-8 h-8 border-3 border-primary/20 border-t-primary rounded-full animate-spin mb-3"></div>
      <p class="text-sm text-ink-muted">Loading...</p>
    </div>

    <!-- Attendance List -->
    <div v-else-if="attendanceRecords.length > 0" class="bg-surface rounded-xl border border-border-light overflow-hidden" style="box-shadow: var(--shadow-card)">
      <div class="overflow-x-auto">
        <table class="w-full min-w-[600px]">
          <thead>
            <tr class="border-b-2 border-border-medium bg-page">
              <th class="text-left py-3 px-4 text-[0.7rem] font-bold text-ink-muted uppercase tracking-wider w-10">#</th>
              <th class="text-left py-3 px-4 text-[0.7rem] font-bold text-ink-muted uppercase tracking-wider">Student</th>
              <th class="text-center py-3 px-4 text-[0.7rem] font-bold text-ink-muted uppercase tracking-wider">Status</th>
              <th class="text-left py-3 px-4 text-[0.7rem] font-bold text-ink-muted uppercase tracking-wider w-28">Time</th>
              <th class="text-left py-3 px-4 text-[0.7rem] font-bold text-ink-muted uppercase tracking-wider">Notes</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(record, idx) in attendanceRecords" :key="record.student_id"
              class="border-b border-border-light last:border-b-0 transition-colors"
              :class="record._status === 'absent' ? 'bg-red-50/40' : record._status === 'present' ? 'bg-emerald-50/30' : ''">
              <td class="py-3 px-4 text-sm text-ink-muted">{{ idx + 1 }}</td>
              <td class="py-3 px-4">
                <div class="font-medium text-sm text-ink">{{ record.student_name }}</div>
                <div v-if="record.student_number" class="text-xs text-ink-muted">{{ record.student_number }}</div>
              </td>
              <td class="py-3 px-4">
                <div class="flex items-center justify-center gap-1">
                  <button v-for="s in statuses" :key="s" @click="record._status = s"
                    class="w-8 h-8 rounded-lg text-xs font-bold border-[1.5px] transition-all"
                    :class="record._status === s ? statusConfig[s].color + ' scale-110 shadow-sm' : 'bg-transparent text-ink-muted border-border-light hover:border-border-medium'">
                    {{ statusConfig[s].label }}
                  </button>
                </div>
              </td>
              <td class="py-3 px-4">
                <input v-model="record.arrival_time" type="time"
                  class="w-full rounded-md border border-border-light px-2 py-1.5 text-xs text-ink focus:outline-none focus:border-primary" />
              </td>
              <td class="py-3 px-4">
                <input v-model="record.notes" type="text" placeholder="Notes..."
                  class="w-full rounded-md border border-border-light px-2 py-1.5 text-xs text-ink focus:outline-none focus:border-primary" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Save Bar -->
      <div class="flex items-center justify-between px-5 py-4 bg-page border-t border-border-light">
        <span class="text-sm text-ink-muted">{{ attendanceRecords.length }} students</span>
        <button @click="saveAttendance" :disabled="saving || !allMarked"
          class="px-6 py-2.5 bg-primary text-ink-inverse rounded-xl text-sm font-semibold hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-all inline-flex items-center gap-2">
          <svg v-if="saving" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
          {{ saving ? 'Saving...' : 'Save Attendance' }}
        </button>
      </div>
    </div>

    <!-- Empty States -->
    <div v-else-if="selectedSectionId && !loading" class="bg-surface rounded-xl border border-border-light p-12 text-center" style="box-shadow: var(--shadow-card)">
      <div class="text-4xl mb-3">📋</div>
      <p class="text-ink-muted text-sm">No students enrolled in this section yet.</p>
    </div>
    <div v-else-if="!selectedSectionId" class="bg-surface rounded-xl border border-border-light p-12 text-center" style="box-shadow: var(--shadow-card)">
      <div class="text-4xl mb-3">👆</div>
      <p class="text-ink font-medium mb-1">Select a Section</p>
      <p class="text-ink-muted text-sm">Choose a section above to start recording attendance.</p>
    </div>

    <!-- Summary Modal -->
    <div v-if="showSummary && summaryData" class="admin-modal-overlay" @click.self="showSummary = false">
      <div class="admin-modal admin-modal-lg">
        <div class="flex items-center justify-between mb-5">
          <h2 class="!mb-0">Attendance Summary</h2>
          <button @click="showSummary = false" class="p-1.5 rounded-lg hover:bg-page text-ink-muted">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="mb-4 flex items-center gap-4 text-sm">
          <span class="text-ink-muted">{{ summaryData.course_name }}</span>
          <span class="text-ink-muted">•</span>
          <span class="text-ink-muted">{{ summaryData.total_sessions }} sessions recorded</span>
        </div>
        <div class="overflow-x-auto rounded-lg border border-border-light">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-page border-b border-border-medium">
                <th class="text-left py-2.5 px-4 text-[0.7rem] font-bold text-ink-muted uppercase">Student</th>
                <th class="text-center py-2.5 px-3 text-[0.7rem] font-bold text-emerald-700 uppercase">Present</th>
                <th class="text-center py-2.5 px-3 text-[0.7rem] font-bold text-red-700 uppercase">Absent</th>
                <th class="text-center py-2.5 px-3 text-[0.7rem] font-bold text-amber-700 uppercase">Late</th>
                <th class="text-center py-2.5 px-3 text-[0.7rem] font-bold text-blue-700 uppercase">Excused</th>
                <th class="text-center py-2.5 px-3 text-[0.7rem] font-bold text-ink-muted uppercase">Rate</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in summaryData.students" :key="s.student_id" class="border-b border-border-light last:border-b-0">
                <td class="py-2.5 px-4 font-medium text-ink">{{ s.student_id.slice(0, 8) }}...</td>
                <td class="py-2.5 px-3 text-center text-emerald-700 font-semibold">{{ s.present }}</td>
                <td class="py-2.5 px-3 text-center text-red-700 font-semibold">{{ s.absent }}</td>
                <td class="py-2.5 px-3 text-center text-amber-700 font-semibold">{{ s.late }}</td>
                <td class="py-2.5 px-3 text-center text-blue-700 font-semibold">{{ s.excused }}</td>
                <td class="py-2.5 px-3 text-center">
                  <span class="inline-block px-2 py-0.5 rounded-full text-xs font-bold"
                    :class="s.attendance_rate >= 80 ? 'bg-emerald-100 text-emerald-700' : s.attendance_rate >= 60 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'">
                    {{ s.attendance_rate }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
