<script setup>
import { ref, onMounted, computed } from 'vue'
import { getMyAssignments } from '../../services/api.js'
import Icons from '../../components/icon/Icons.vue'

const loading = ref(true)
const assignments = ref([])

onMounted(async () => {
    loading.value = true
    try {
        const res = await getMyAssignments()
        assignments.value = res.data.assignments || []
    } catch (error) {
        console.warn('Could not load assignments:', error.response?.data?.detail || error.message)
    } finally {
        loading.value = false
    }
})

const getStatusColor = (status, submitted) => {
    if (!submitted) return 'bg-slate-100 text-slate-600'
    switch (status) {
        case 'submitted': return 'bg-info/10 text-info'
        case 'graded': return 'bg-success/10 text-success'
        case 'late': return 'bg-warning/10 text-warning'
        default: return 'bg-slate-100 text-slate-600'
    }
}

const formatDate = (dateString) => {
    if (!dateString) return 'No due date'
    return new Date(dateString).toLocaleDateString(undefined, {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    })
}
</script>

<template>
    <div class="space-y-6">
        <div>
            <h1 class="text-2xl font-bold text-ink tracking-tight">My Assignments</h1>
            <p class="text-sm text-ink-muted mt-0.5">View and manage your course work</p>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="text-center py-12 text-ink-muted">
            <Icons name="mdi-loading" class="animate-spin w-8 h-8 mb-2" />
            <p>Loading assignments...</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="assignments.length === 0"
            class="bg-surface border border-border-light rounded-2xl shadow-card p-12 text-center text-ink-muted">
            <div
                class="w-16 h-16 rounded-full bg-surface border-2 border-dashed border-border-medium flex items-center justify-center mx-auto mb-4">
                <Icons name="mdi-clipboard-check-outline" class="text-2xl opacity-50" />
            </div>
            <h3 class="text-lg font-medium text-ink mb-1">All Caught Up!</h3>
            <p class="text-sm">No pending assignments found for your enrolled courses.</p>
        </div>

        <!-- Assignments List -->
        <div v-else class="grid gap-4">
            <div v-for="(asn, i) in assignments" :key="asn.assignment_id"
                class="bg-surface border border-border-light rounded-xl p-5 shadow-sm hover:shadow-card hover:-translate-y-0.5 transition-all duration-200 animate-fade-in"
                :class="'delay-' + Math.min(i, 5)">

                <div class="flex justify-between items-start gap-4">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-1">
                            <span
                                class="px-2 py-0.5 rounded text-[0.65rem] font-bold uppercase tracking-wider bg-primary/10 text-primary">
                                {{ asn.course_code }}
                            </span>
                            <span class="text-xs text-ink-muted flex items-center gap-1">
                                <Icons name="mdi-account-school-outline" class="text-[1rem]" /> {{ asn.instructor_name
                                }}
                            </span>
                        </div>
                        <h3 class="text-lg font-semibold text-ink m-0 mb-1">{{ asn.assignment_name }}</h3>
                        <p v-if="asn.description" class="text-sm text-ink-secondary mb-3 line-clamp-2">{{
                            asn.description }}</p>

                        <div class="flex flex-wrap items-center gap-4 text-xs text-ink-muted mt-2">
                            <span
                                class="flex items-center gap-1.5 bg-page px-2 py-1 rounded-md border border-border-light">
                                <Icons name="mdi-calendar-clock" class="text-coral" />
                                <span :class="{ 'text-coral font-medium': !asn.submitted }">Due: {{
                                    formatDate(asn.due_date) }}</span>
                            </span>
                            <span class="flex items-center gap-1.5">
                                <Icons name="mdi-scale-balance" /> {{ asn.weight_percentage }}% of grade
                            </span>
                            <span class="flex items-center gap-1.5">
                                <Icons name="mdi-star-circle-outline" /> {{ asn.max_points }} pts
                            </span>
                        </div>
                    </div>

                    <div class="flex flex-col items-end gap-2 shrink-0">
                        <span v-if="asn.submitted"
                            :class="['px-2.5 py-1 rounded-full text-xs font-semibold', getStatusColor(asn.submission_status, true)]">
                            {{ asn.submission_status === 'graded' ? `${asn.points_earned} / ${asn.max_points}` :
                                'Submitted' }}
                        </span>
                        <span v-else
                            class="px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-500 border border-slate-200">
                            Not Submitted
                        </span>

                        <button v-if="!asn.submitted"
                            class="mt-1 inline-flex items-center gap-1.5 px-4 py-1.5 bg-coral text-white border-none rounded-lg font-sans text-xs font-bold cursor-pointer transition-all hover:bg-coral-hover hover:shadow-lg">
                            <Icons name="mdi-upload" /> Submit
                        </button>
                        <button v-else
                            class="mt-1 inline-flex items-center gap-1.5 px-4 py-1.5 bg-white text-primary border border-primary/20 rounded-lg font-sans text-xs font-medium cursor-pointer transition-all hover:bg-primary/5">
                            <Icons name="mdi-eye" /> View
                        </button>
                    </div>
                </div>

                <!-- Team/Topic Section (Placeholder for future feature as requested) -->
                <div v-if="asn.is_group_assignment"
                    class="mt-4 pt-4 border-t border-border-light flex items-center gap-2">
                    <div class="w-6 h-6 rounded-full bg-info/10 text-info flex items-center justify-center text-xs">
                        <Icons name="mdi-account-group" />
                    </div>
                    <span class="text-xs font-medium text-ink-secondary">Group Assignment</span>
                </div>
            </div>
        </div>
    </div>
</template>
