<script setup>
import { ref, onMounted } from 'vue'
import { getHealth, getHealthDb } from '../services/api.js'
import { getDepartments } from '../services/api.js'
import { getCourses } from '../services/api.js'
import { getStudents, getPrograms, getFaculty } from '../services/api.js'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js'
import { Bar } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const healthStatus = ref(null)
const dbStatus = ref(null)
const loading = ref(true)
const departments = ref([null])
const courses = ref([null])
const students = ref(null)
const teachers = ref(null)
const payments = ref([])

// Chart Data
const chartData = ref({
  labels: [],
  datasets: [{ data: [] }]
})
const chartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    title: {
      display: true,
      text: 'Students per Program',
      color: '#1F2937',
      font: { size: 14, weight: '600', family: 'Inter, sans-serif' }
    },
    tooltip: {
      backgroundColor: '#1f2937',
      titleColor: '#f9fafb',
      bodyColor: '#f9fafb',
      padding: 10,
      cornerRadius: 6,
      titleFont: { family: 'Inter, sans-serif' },
      bodyFont: { family: 'Inter, sans-serif' }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: { color: '#F3F4F6', drawBorder: false },
      ticks: { color: '#9CA3AF', font: { family: 'Inter, sans-serif', size: 11 } }
    },
    x: {
      grid: { display: false },
      ticks: { color: '#9CA3AF', font: { family: 'Inter, sans-serif', size: 11 } }
    }
  }
})
const chartLoaded = ref(false)

// Soft accent palette for bars
const barColors = [
  '#6366F1', '#8B5CF6', '#EC4899', '#14B8A6',
  '#F59E0B', '#3B82F6', '#10B981', '#EF4444',
  '#06B6D4', '#84CC16'
]

onMounted(async () => {
  try {
    const [departmentsRes, coursesRes, studentsRes, programsRes, facultyRes, healthRes, dbRes] = await Promise.allSettled([
      getDepartments(),
      getCourses(),
      getStudents(0, 100),
      getPrograms(0, 200),
      getFaculty(0, 1),
      getHealth(),
      getHealthDb()
    ])

    departments.value = departmentsRes.status === 'fulfilled' ? departmentsRes.value.data : [null]
    courses.value = coursesRes.status === 'fulfilled' ? coursesRes.value.data : [null]
    students.value = studentsRes.status === 'fulfilled' ? studentsRes.value.data : null
    teachers.value = facultyRes.status === 'fulfilled' ? facultyRes.value.data : null

    // Process Chart Data
    if (studentsRes.status === 'fulfilled' && programsRes.status === 'fulfilled') {
      const studentsData = studentsRes.value.data.students
      const programs = programsRes.value.data.programs

      const programCounts = {}
      studentsData.forEach(student => {
        const program = programs.find(p => p.program_id === student.program_id)
        const programName = program ? program.program_code : 'Unknown'
        programCounts[programName] = (programCounts[programName] || 0) + 1
      })

      const bgColors = Object.keys(programCounts).map((_, i) => barColors[i % barColors.length])

      chartData.value = {
        labels: Object.keys(programCounts),
        datasets: [
          {
            label: 'Students',
            backgroundColor: bgColors,
            borderColor: 'transparent',
            borderWidth: 0,
            hoverBackgroundColor: bgColors.map(c => c + 'CC'),
            borderRadius: 6,
            data: Object.values(programCounts)
          }
        ]
      }
      chartLoaded.value = true

      // Calculate Payments per Program
      const paymentMap = {}
      studentsData.forEach(student => {
        const program = programs.find(p => p.program_id === student.program_id)
        const programName = program ? program.program_code : 'Unknown'
        const payment = student.account ? parseFloat(student.account.total_payments) : 0

        if (!paymentMap[programName]) {
          paymentMap[programName] = { totalPayment: 0, programDetails: program }
        }
        paymentMap[programName].totalPayment += payment
      })

      payments.value = Object.entries(paymentMap).map(([programName, { totalPayment, programDetails }]) => ({
        program: programName,
        credits: programDetails ? programDetails.total_credits_required : '-',
        duration: programDetails ? `${programDetails.duration_years} Years` : '-',
        totalPayment: totalPayment.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
      }))
    }

    healthStatus.value = healthRes.status === 'fulfilled' ? healthRes.value.data : { status: 'error' }
    dbStatus.value = dbRes.status === 'fulfilled' ? dbRes.value.data : { status: 'error', database: 'unreachable' }
  } catch (error) {
    console.error('Error fetching dashboard data:', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <!-- Page Header -->
    <div class="admin-page-header">
      <div>
        <h1 class="text-2xl font-bold text-ink">Dashboard</h1>
        <p class="text-sm text-ink-muted mt-0.5">System overview and key metrics</p>
      </div>
    </div>
    <!-- Loading -->
    <div v-if="loading" class="admin-loading">Loading system status...</div>

    <div v-else>
      <!-- Stats Grid -->
      <div class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6">
        <!-- API Status -->
        <div class="cm-card p-5 border border-border-light rounded-xl hover:border-primary hover:shadow-lg transition-all transform hover:scale-105 duration-200">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-semibold uppercase tracking-wide text-ink-muted">API Status</span>
            <span class="admin-badge"
              :class="healthStatus?.status === 'healthy' ? 'admin-badge-active' : 'admin-badge-inactive'">
              {{ healthStatus?.status || 'unknown' }}
            </span>
          </div>
          <p class="text-lg font-semibold text-ink">{{ healthStatus?.app || 'N/A' }}</p>
          <p class="text-xs text-ink-muted mt-1">v{{ healthStatus?.version || '?' }}</p>
        </div>

        <!-- DB Connection -->
        <div class="cm-card p-5 border border-border-light rounded-xl hover:border-primary hover:shadow-lg transition-all transform hover:scale-105 duration-200">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-semibold uppercase tracking-wide text-ink-muted">DB Connection</span>
            <span class="admin-badge"
              :class="dbStatus?.status === 'healthy' ? 'admin-badge-active' : 'admin-badge-inactive'">
              {{ dbStatus?.database || 'unknown' }}
            </span>
          </div>
          <p class="text-lg font-semibold text-ink">PostgreSQL</p>
          <p class="text-xs text-ink-muted mt-1">v{{ dbStatus?.version || '?' }}</p>
        </div>

        <!-- Departments -->
        <div class="cm-card p-5 border border-border-light rounded-xl hover:border-primary hover:shadow-lg transition-all transform hover:scale-105 duration-200">
          <span class="text-xs font-semibold uppercase tracking-wide text-ink-muted">Departments</span>
          <p v-if="departments && departments.total !== undefined" class="text-3xl font-bold text-ink mt-2">
            {{ departments.total }}
          </p>
          <p v-else class="text-3xl font-bold text-border-strong mt-2">-</p>
          <p class="text-xs text-ink-muted mt-1">Total active</p>
        </div>

        <!-- Courses -->
        <div class="cm-card p-5 border border-border-light rounded-xl hover:border-primary hover:shadow-lg transition-all transform hover:scale-105 duration-200">
          <span class="text-xs font-semibold uppercase tracking-wide text-ink-muted">Courses</span>
          <p v-if="courses && courses.total !== undefined" class="text-3xl font-bold text-ink mt-2">
            {{ courses.total }}
          </p>
          <p v-else class="text-3xl font-bold text-border-strong mt-2">-</p>
          <p class="text-xs text-ink-muted mt-1">Total active</p>
        </div>
      </div>

      <!-- Welcome Card -->
      <div class="cm-card-static p-4 sm:p-6 mb-6">
        <h2 class="text-base font-semibold text-ink mb-2">Welcome to School Management System</h2>
        <p class="text-sm text-ink-secondary leading-relaxed">
          A comprehensive university management system built with
          <strong>FastAPI</strong> (backend), <strong>Vue 3</strong> (frontend),
          <strong>Tailwind CSS v4</strong> (styling), and <strong>PostgreSQL 18</strong> (database).
        </p>
        <div class="mt-4 flex flex-col sm:flex-row gap-2 sm:gap-3">
          <Router-Link to="/departments" class="cm-btn-primary">
            View Departments
          </Router-Link>
          <Router-Link to="/courses" class="cm-btn-secondary">
            View Courses
          </Router-Link>
        </div>
      </div>

      <!-- Enrollment Chart -->
      <div class="cm-card-static p-4 sm:p-6 mb-6">
        <h2 class="text-base font-semibold text-ink mb-4">Enrollment Students</h2>
        <div v-if="chartLoaded" class="h-48 sm:h-64">
          <Bar :data="chartData" :options="chartOptions" />
        </div>
        <div v-else class="text-sm text-ink-muted text-center py-8">Loading chart data...</div>

        <!-- Quick Stats Row -->
        <div class="mt-6 flex flex-wrap gap-3 justify-center">
          <div class="flex items-center gap-2 px-4 py-1.5 rounded-full border border-border-light bg-primary-50">
            <div class="w-2 h-2 rounded-full bg-primary"></div>
            <span class="text-xs font-medium text-primary-dark">
              <strong>{{ students?.total || 0 }}</strong> Students
            </span>
          </div>
          <div class="flex items-center gap-2 px-4 py-1.5 rounded-full border border-border-light bg-success-light">
            <div class="w-2 h-2 rounded-full bg-success"></div>
            <span class="text-xs font-medium text-ink-secondary">
              <strong>{{ teachers?.total || 0 }}</strong> Teachers
            </span>
          </div>
          <div class="flex items-center gap-2 px-4 py-1.5 rounded-full border border-border-light bg-info-light">
            <div class="w-2 h-2 rounded-full bg-info"></div>
            <span class="text-xs font-medium text-ink-secondary">
              <strong>{{ courses?.total || 0 }}</strong> Courses
            </span>
          </div>
        </div>
      </div>

      <!-- Financial Payment Table -->
      <div class="admin-table-card">
        <div class="p-5 border-b border-border-light">
          <h2 class="text-base font-semibold text-ink">Financial Payment by Program</h2>
          <p class="text-xs text-ink-muted mt-0.5">Overview of payments and program details</p>
        </div>

        <div class="overflow-x-auto">
          <table class="admin-table">
            <thead>
              <tr>
                <th>Program</th>
                <th class="text-center">Credits</th>
                <th class="text-center">Duration</th>
                <th class="text-right">Total Payment</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="payment in payments" :key="payment.program">
                <td>
                  <span class="font-medium text-ink">{{ payment.program }}</span>
                </td>
                <td class="text-center">
                  <span class="cm-badge cm-badge-primary">{{ payment.credits }}</span>
                </td>
                <td class="text-center">{{ payment.duration }}</td>
                <td class="text-right font-semibold text-ink">{{ payment.totalPayment }}</td>
              </tr>
              <tr v-if="payments.length === 0">
                <td colspan="4" class="text-center py-8 text-ink-muted">
                  No payment records found.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
