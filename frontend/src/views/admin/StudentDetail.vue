<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getEnrollments, getStudent, getStudentAccount } from '../../services/api.js'
import Icons from '../../components/icon/Icons.vue'

const route = useRoute()
const studentId = route.params.id

const loading = ref(true)
const student = ref(null)
const enrollments = ref([])
const account = ref(null)
const activeTab = ref('enrollments')

onMounted(async () => {
    loading.value = true
    try {
        const [studentRes, enrollmentsRes, accountRes] = await Promise.allSettled([
            getStudent(studentId),
            getEnrollments(0, 100, studentId),
            getStudentAccount(studentId)
        ])

        if (studentRes.status === 'fulfilled') student.value = studentRes.value.data
        if (enrollmentsRes.status === 'fulfilled') enrollments.value = enrollmentsRes.value.data.enrollments || []
        if (accountRes.status === 'fulfilled') account.value = accountRes.value.data
    } catch (error) {
        console.error('Error fetching student details:', error)
    } finally {
        loading.value = false
    }
})

const studentName = computed(() => {
    if (!student.value?.user?.personal_info) return 'Student'
    const { first_name, last_name } = student.value.user.personal_info
    return `${first_name} ${last_name}`
})

const activeEnrollmentsCount = computed(() =>
    enrollments.value.filter(enr => enr.enrollment_status === 'enrolled').length
)

const completedEnrollmentsCount = computed(() =>
    enrollments.value.filter(enr => enr.enrollment_status === 'completed').length
)

const currentBalance = computed(() => Number(account.value?.balance || 0).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
}))

const accountStatus = computed(() => {
    if (!account.value) return 'No account'
    return account.value.has_hold ? 'On Hold' : 'Clear'
})

const formatDate = (value) => value ? new Date(value).toLocaleDateString() : 'N/A'
</script>

<template>
    <div class="space-y-6">
        <div>
            <router-link to="/students"
                class="inline-flex items-center gap-2 rounded-lg border border-border-light bg-surface px-4 py-2 text-sm font-medium text-ink-muted transition-all hover:text-ink hover:shadow-sm">
                <Icons name="mdi-arrow-left" class="w-4 h-4" />
                Back
            </router-link>
        </div>

        <div v-if="loading" class="text-center py-12 text-ink-muted">
            <Icons name="mdi-loading" class="animate-spin w-8 h-8 mb-2" />
            <p>Loading details...</p>
        </div>

        <div v-else-if="!student" class="text-center py-12 text-ink-muted">
            <p>Student not found.</p>
        </div>

        <div v-else class="space-y-6">
            <div
                class="bg-surface border border-border-light rounded-2xl p-8 shadow-card flex flex-col md:flex-row items-start md:items-center gap-6 animate-fade-in">
                <div
                    class="w-20 h-20 rounded-full bg-primary/10 text-primary flex items-center justify-center text-3xl font-bold">
                    {{ studentName.charAt(0) }}
                </div>
                <div class="flex-1">
                    <h1 class="text-2xl font-bold text-ink mb-1">{{ studentName }}</h1>
                    <div class="flex flex-wrap gap-2 text-sm text-ink-muted">
                        <span class="px-2.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-slate-600">
                            {{ student.student_number }}
                        </span>
                        <span class="px-2.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-slate-600">
                            {{ student.program?.program_code || 'No Program' }}
                        </span>
                        <span class="px-2.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-slate-600">
                            {{ student.enrollment_status }}
                        </span>
                    </div>
                    <div class="mt-4 flex gap-6 text-sm">
                        <div>
                            <span class="block font-bold text-xl text-ink">{{ activeEnrollmentsCount }}</span>
                            <span class="text-ink-muted">Active Courses</span>
                        </div>
                        <div>
                            <span class="block font-bold text-xl text-ink">{{ completedEnrollmentsCount }}</span>
                            <span class="text-ink-muted">Completed Courses</span>
                        </div>
                        <div>
                            <span class="block font-bold text-xl text-ink">${{ currentBalance }}</span>
                            <span class="text-ink-muted">Balance</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <div class="bg-surface border border-border-light rounded-xl p-5 shadow-sm">
                    <p class="text-xs uppercase tracking-wider text-ink-muted mb-2">Email</p>
                    <p class="text-sm font-medium text-ink break-all">{{ student.user?.email || 'N/A' }}</p>
                </div>
                <div class="bg-surface border border-border-light rounded-xl p-5 shadow-sm">
                    <p class="text-xs uppercase tracking-wider text-ink-muted mb-2">Program</p>
                    <p class="text-sm font-medium text-ink">{{ student.program?.program_name || 'N/A' }}</p>
                </div>
                <div class="bg-surface border border-border-light rounded-xl p-5 shadow-sm">
                    <p class="text-xs uppercase tracking-wider text-ink-muted mb-2">Standing</p>
                    <p class="text-sm font-medium text-ink">{{ student.academic_standing }}</p>
                </div>
                <div class="bg-surface border border-border-light rounded-xl p-5 shadow-sm">
                    <p class="text-xs uppercase tracking-wider text-ink-muted mb-2">Enrollment Date</p>
                    <p class="text-sm font-medium text-ink">{{ formatDate(student.enrollment_date) }}</p>
                </div>
            </div>

            <div class="border-b border-border-light">
                <div class="flex gap-6">
                    <button @click="activeTab = 'enrollments'" class="pb-3 text-sm font-medium transition-all relative"
                        :class="activeTab === 'enrollments' ? 'text-primary' : 'text-ink-muted hover:text-ink'">
                        Enrollments
                        <div v-if="activeTab === 'enrollments'"
                            class="absolute bottom-0 left-0 w-full h-0.5 bg-primary rounded-t-full"></div>
                    </button>
                    <button @click="activeTab = 'account'" class="pb-3 text-sm font-medium transition-all relative"
                        :class="activeTab === 'account' ? 'text-primary' : 'text-ink-muted hover:text-ink'">
                        Account
                        <div v-if="activeTab === 'account'"
                            class="absolute bottom-0 left-0 w-full h-0.5 bg-primary rounded-t-full"></div>
                    </button>
                </div>
            </div>

            <div v-if="activeTab === 'enrollments'" class="animate-fade-in">
                <div class="grid gap-4">
                    <div v-for="enrollment in enrollments" :key="enrollment.enrollment_id"
                        class="bg-surface border border-border-light rounded-xl p-5 shadow-sm hover:shadow-card transition-all">
                        <div class="flex justify-between items-start gap-4">
                            <div>
                                <div class="flex items-center gap-2 mb-1">
                                    <span
                                        class="px-2 py-0.5 rounded text-[0.65rem] font-bold uppercase tracking-wider bg-primary/10 text-primary">
                                        {{ enrollment.section?.course?.course_code || 'Course' }}
                                    </span>
                                    <span class="text-xs text-ink-muted">
                                        {{ enrollment.section?.term?.term_name || 'Term N/A' }}
                                    </span>
                                </div>
                                <h3 class="text-lg font-semibold text-ink">
                                    {{ enrollment.section?.course?.course_name || 'Course Name N/A' }}
                                </h3>
                                <p class="text-sm text-ink-muted mt-1">
                                    Section {{ enrollment.section?.section_number || 'N/A' }}
                                    <span class="mx-2">·</span>
                                    {{ enrollment.section?.schedule_pattern || 'Schedule TBA' }}
                                </p>
                            </div>
                            <div class="text-right">
                                <span class="inline-flex px-2.5 py-1 rounded-full text-xs font-semibold"
                                    :class="enrollment.enrollment_status === 'completed'
                                        ? 'bg-success/10 text-success'
                                        : 'bg-slate-100 text-slate-600'">
                                    {{ enrollment.enrollment_status }}
                                </span>
                                <p class="text-xs text-ink-muted mt-2">Grade: {{ enrollment.final_grade || enrollment.grade || '-' }}</p>
                            </div>
                        </div>
                    </div>
                    <div v-if="enrollments.length === 0"
                        class="text-center py-8 text-ink-muted bg-surface rounded-xl border border-border-light border-dashed">
                        <p>No enrollments found.</p>
                    </div>
                </div>
            </div>

            <div v-if="activeTab === 'account'" class="animate-fade-in">
                <div v-if="account" class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                    <div class="bg-surface border border-border-light rounded-xl p-5 shadow-sm">
                        <p class="text-xs uppercase tracking-wider text-ink-muted mb-2">Account Number</p>
                        <p class="text-sm font-medium text-ink">{{ account.account_number }}</p>
                    </div>
                    <div class="bg-surface border border-border-light rounded-xl p-5 shadow-sm">
                        <p class="text-xs uppercase tracking-wider text-ink-muted mb-2">Balance</p>
                        <p class="text-sm font-medium text-ink">${{ currentBalance }}</p>
                    </div>
                    <div class="bg-surface border border-border-light rounded-xl p-5 shadow-sm">
                        <p class="text-xs uppercase tracking-wider text-ink-muted mb-2">Status</p>
                        <p class="text-sm font-medium text-ink">{{ accountStatus }}</p>
                    </div>
                    <div class="bg-surface border border-border-light rounded-xl p-5 shadow-sm">
                        <p class="text-xs uppercase tracking-wider text-ink-muted mb-2">Hold Reason</p>
                        <p class="text-sm font-medium text-ink">{{ account.hold_reason || 'None' }}</p>
                    </div>
                </div>
                <div v-else
                    class="text-center py-8 text-ink-muted bg-surface rounded-xl border border-border-light border-dashed">
                    <p>No student account found.</p>
                </div>
            </div>
        </div>
    </div>
</template>
