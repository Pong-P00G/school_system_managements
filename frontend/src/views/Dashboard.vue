<script setup>
import { ref, onMounted } from 'vue'
import { getHealth, getHealthDb, getDepartments, getCourses, getStudents, getPrograms, getFaculty } from '../services/api.js'
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js'
import { Bar } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const loading = ref(true)
const healthStatus = ref(null)
const dbStatus = ref(null)
const stats = ref({ departments: 0, courses: 0, students: 0, teachers: 0 })
const chartData = ref({ labels: [], datasets: [{ data: [] }] })
const chartLoaded = ref(false)
const payments = ref([])

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { backgroundColor: '#2C2C2C', padding: 10, cornerRadius: 8 },
  },
  scales: {
    y: { beginAtZero: true, grid: { color: '#f3f4f6' }, ticks: { color: '#8c9197' } },
    x: { grid: { display: false }, ticks: { color: '#8c9197' } },
  },
}

const barColors = ['#2F4F4F', '#3d6363', '#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4']

onMounted(async () => {
  try {
    const [deptRes, courseRes, studentRes, progRes, facRes, hRes, dbRes] = await Promise.allSettled([
      getDepartments(), getCourses(), getStudents(0, 200), getPrograms(0, 200), getFaculty(0, 1), getHealth(), getHealthDb(),
    ])

    stats.value.departments = deptRes.status === 'fulfilled' ? deptRes.value.data.total || 0 : 0
    stats.value.courses = courseRes.status === 'fulfilled' ? courseRes.value.data.total || 0 : 0
    stats.value.students = studentRes.status === 'fulfilled' ? studentRes.value.data.total || 0 : 0
    stats.value.teachers = facRes.status === 'fulfilled' ? facRes.value.data.total || 0 : 0
    healthStatus.value = hRes.status === 'fulfilled' ? hRes.value.data : null
    dbStatus.value = dbRes.status === 'fulfilled' ? dbRes.value.data : null

    if (studentRes.status === 'fulfilled' && progRes.status === 'fulfilled') {
      const studentsData = studentRes.value.data.students || []
      const programs = progRes.value.data.programs || []
      const counts = {}
      studentsData.forEach(s => {
        const p = programs.find(pr => pr.program_id === s.program_id)
        const name = p ? p.program_code : 'Other'
        counts[name] = (counts[name] || 0) + 1
      })
      chartData.value = {
        labels: Object.keys(counts),
        datasets: [{ label: 'Students', data: Object.values(counts), backgroundColor: Object.keys(counts).map((_, i) => barColors[i % barColors.length]), borderRadius: 6 }],
      }
      chartLoaded.value = true

      // Payment summary
      const payMap = {}
      studentsData.forEach(s => {
        const p = programs.find(pr => pr.program_id === s.program_id)
        const name = p ? p.program_code : 'Other'
        const pay = s.account ? parseFloat(s.account.total_payments || 0) : 0
        if (!payMap[name]) payMap[name] = { total: 0, program: p }
        payMap[name].total += pay
      })
      payments.value = Object.entries(payMap).map(([name, { total, program }]) => ({
        name, credits: program?.total_credits_required || '-', duration: program?.duration_years ? `${program.duration_years}y` : '-',
        total: total.toLocaleString('en-US', { style: 'currency', currency: 'USD' }),
      }))
    }
  } catch (e) { console.error(e) }
  finally { loading.value = false }
})
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-[1.75rem] font-bold text-ink tracking-tight">Dashboard</h1>
      <p class="text-sm text-ink-muted mt-0.5">System overview and key metrics</p>
    </div>

    <div v-if="loading" class="admin-loading">Loading dashboard...</div>

    <div v-else>
      <!-- Stat Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-surface rounded-xl border border-border-light p-5 hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300">
          <div class="flex items-center justify-between mb-3">
            <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <svg class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/></svg>
            </div>
          </div>
          <p class="text-2xl font-bold text-ink">{{ stats.students }}</p>
          <p class="text-xs text-ink-muted font-medium mt-1">Students</p>
        </div>

        <div class="bg-surface rounded-xl border border-border-light p-5 hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300">
          <div class="flex items-center justify-between mb-3">
            <div class="w-10 h-10 rounded-lg bg-success/10 flex items-center justify-center">
              <svg class="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
            </div>
          </div>
          <p class="text-2xl font-bold text-ink">{{ stats.departments }}</p>
          <p class="text-xs text-ink-muted font-medium mt-1">Departments</p>
        </div>

        <div class="bg-surface rounded-xl border border-border-light p-5 hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300">
          <div class="flex items-center justify-between mb-3">
            <div class="w-10 h-10 rounded-lg bg-info/10 flex items-center justify-center">
              <svg class="w-5 h-5 text-info" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
            </div>
          </div>
          <p class="text-2xl font-bold text-ink">{{ stats.courses }}</p>
          <p class="text-xs text-ink-muted font-medium mt-1">Courses</p>
        </div>

        <div class="bg-surface rounded-xl border border-border-light p-5 hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300">
          <div class="flex items-center justify-between mb-3">
            <div class="w-10 h-10 rounded-lg bg-warning/10 flex items-center justify-center">
              <svg class="w-5 h-5 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
            </div>
          </div>
          <p class="text-2xl font-bold text-ink">{{ stats.teachers }}</p>
          <p class="text-xs text-ink-muted font-medium mt-1">Faculty</p>
        </div>
      </div>

      <!-- System Health -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div class="bg-surface rounded-xl border border-border-light p-5">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-xs font-bold text-ink-muted uppercase tracking-wider">API Server</p>
              <p class="text-sm font-semibold text-ink mt-1">{{ healthStatus?.app || 'School System' }}</p>
              <p class="text-xs text-ink-muted mt-0.5">v{{ healthStatus?.version || '?' }}</p>
            </div>
            <span class="px-2.5 py-1 rounded-full text-[0.7rem] font-bold"
              :class="healthStatus?.status === 'healthy' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'">
              {{ healthStatus?.status || 'unknown' }}
            </span>
          </div>
        </div>
        <div class="bg-surface rounded-xl border border-border-light p-5">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-xs font-bold text-ink-muted uppercase tracking-wider">Database</p>
              <p class="text-sm font-semibold text-ink mt-1">PostgreSQL</p>
              <p class="text-xs text-ink-muted mt-0.5">{{ dbStatus?.version || 'N/A' }}</p>
            </div>
            <span class="px-2.5 py-1 rounded-full text-[0.7rem] font-bold"
              :class="dbStatus?.status === 'healthy' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'">
              {{ dbStatus?.database || 'unknown' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Chart -->
      <div class="bg-surface rounded-xl border border-border-light p-5 mb-6" style="box-shadow: var(--shadow-card)">
        <h2 class="text-base font-semibold text-ink mb-4">Students per Program</h2>
        <div v-if="chartLoaded" class="h-52 sm:h-64">
          <Bar :data="chartData" :options="chartOptions" />
        </div>
        <div v-else class="h-52 flex items-center justify-center text-sm text-ink-muted">No enrollment data</div>
      </div>

      <!-- Quick Links -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <router-link to="/departments" class="bg-surface rounded-xl border border-border-light p-4 text-center hover:border-primary hover:shadow-sm transition-all group">
          <div class="text-2xl mb-1">🏛️</div>
          <p class="text-sm font-medium text-ink group-hover:text-primary transition-colors">Departments</p>
        </router-link>
        <router-link to="/courses" class="bg-surface rounded-xl border border-border-light p-4 text-center hover:border-primary hover:shadow-sm transition-all group">
          <div class="text-2xl mb-1">📚</div>
          <p class="text-sm font-medium text-ink group-hover:text-primary transition-colors">Courses</p>
        </router-link>
        <router-link to="/students" class="bg-surface rounded-xl border border-border-light p-4 text-center hover:border-primary hover:shadow-sm transition-all group">
          <div class="text-2xl mb-1">🎓</div>
          <p class="text-sm font-medium text-ink group-hover:text-primary transition-colors">Students</p>
        </router-link>
        <router-link to="/attendance" class="bg-surface rounded-xl border border-border-light p-4 text-center hover:border-primary hover:shadow-sm transition-all group">
          <div class="text-2xl mb-1">📋</div>
          <p class="text-sm font-medium text-ink group-hover:text-primary transition-colors">Attendance</p>
        </router-link>
      </div>

      <!-- Payment Table -->
      <div v-if="payments.length > 0" class="bg-surface rounded-xl border border-border-light overflow-hidden" style="box-shadow: var(--shadow-card)">
        <div class="px-5 py-4 border-b border-border-light">
          <h2 class="text-base font-semibold text-ink">Payments by Program</h2>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full min-w-100">
            <thead>
              <tr class="bg-page border-b border-border-medium">
                <th class="text-left py-3 px-5 text-[0.7rem] font-bold text-ink-muted uppercase tracking-wider">Program</th>
                <th class="text-center py-3 px-4 text-[0.7rem] font-bold text-ink-muted uppercase tracking-wider">Credits</th>
                <th class="text-center py-3 px-4 text-[0.7rem] font-bold text-ink-muted uppercase tracking-wider">Duration</th>
                <th class="text-right py-3 px-5 text-[0.7rem] font-bold text-ink-muted uppercase tracking-wider">Total Paid</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in payments" :key="p.name" class="border-b border-border-light last:border-b-0 hover:bg-page/50 transition-colors">
                <td class="py-3 px-5 text-sm font-semibold text-primary">{{ p.name }}</td>
                <td class="py-3 px-4 text-sm text-center text-ink-secondary">{{ p.credits }}</td>
                <td class="py-3 px-4 text-sm text-center text-ink-secondary">{{ p.duration }}</td>
                <td class="py-3 px-5 text-sm text-right font-semibold text-ink">{{ p.total }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
