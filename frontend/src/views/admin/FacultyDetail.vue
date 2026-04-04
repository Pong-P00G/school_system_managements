<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { getFacultyById, getFacultySections, getFacultyAssignments } from '../../services/api.js'
import Icons from '../../components/icon/Icons.vue'

const route = useRoute()
const facultyId = route.params.id

const loading = ref(true)
const faculty = ref(null)
const sections = ref([])
const assignments = ref([])
const activeTab = ref('classes') // classes, assignments

onMounted(async () => {
    loading.value = true
    try {
        const [facRes, secRes, asnRes] = await Promise.allSettled([
            getFacultyById(facultyId),
            getFacultySections(facultyId),
            getFacultyAssignments(facultyId)
        ])

        if (facRes.status === 'fulfilled') faculty.value = facRes.value.data
        if (secRes.status === 'fulfilled') sections.value = secRes.value.data.sections || []
        if (asnRes.status === 'fulfilled') assignments.value = asnRes.value.data.assignments || []

    } catch (error) {
        console.error('Error fetching faculty details:', error)
    } finally {
        loading.value = false
    }
})

const totalStudents = computed(() => {
    // Sum up enrolled_count from all sections
    if (!sections.value || !Array.isArray(sections.value)) return 0
    return sections.value.reduce((sum, sec) => sum + (sec.enrolled_count || 0), 0)
})

const activeClassesCount = computed(() => {
    if (!sections.value || !Array.isArray(sections.value)) return 0
    return sections.value.filter(s => s.status === 'active' || s.status === 'published').length
})

const facultyName = computed(() => {
    if (!faculty.value?.user?.personal_info) return 'Faculty Member'
    const { first_name, last_name } = faculty.value.user.personal_info
    return `${first_name} ${last_name}`
})
</script>

<template>
    <div class="space-y-6">
        <div>
            <router-link to="/lecturer"
                class="inline-flex items-center gap-2 rounded-lg border border-border-light bg-surface px-4 py-2 text-sm font-medium text-ink-muted transition-all hover:text-ink hover:shadow-sm">
                <Icons name="mdi-arrow-left" class="w-4 h-4" />
                    Back
            </router-link>
        </div>

        <div v-if="loading" class="text-center py-12 text-ink-muted">
            <Icons name="mdi-loading" class="animate-spin w-8 h-8 mb-2" />
            <p>Loading details...</p>
        </div>

        <div v-else-if="!faculty" class="text-center py-12 text-ink-muted">
            <p>Faculty member not found.</p>
        </div>

        <div v-else class="space-y-6">

            <!-- Profile Header -->
            <div
                class="bg-surface border border-border-light rounded-2xl p-8 shadow-card flex flex-col md:flex-row items-start md:items-center gap-6 animate-fade-in">
                <div
                    class="w-20 h-20 rounded-full bg-primary/10 text-primary flex items-center justify-center text-3xl font-bold">
                    {{ facultyName.charAt(0) }}
                </div>
                <div class="flex-1">
                    <h1 class="text-2xl font-bold text-ink mb-1">{{ facultyName }}</h1>
                    <div class="flex flex-wrap gap-2 text-sm text-ink-muted">
                        <span class="px-2.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-slate-600">{{
                            faculty.faculty_rank }}</span>
                        <span class="px-2.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-slate-600">{{
                            faculty.department_id ? 'Dept ID: ' + faculty.department_id : 'No Dept' }}</span>
                        <span class="px-2.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-slate-600">{{
                            faculty.employment_status }}</span>
                    </div>
                    <div class="mt-4 flex gap-6 text-sm">
                        <div>
                            <span class="block font-bold text-xl text-ink">{{ activeClassesCount }}</span>
                            <span class="text-ink-muted">Active Classes</span>
                        </div>
                        <div>
                            <span class="block font-bold text-xl text-ink">{{ totalStudents }}</span>
                            <span class="text-ink-muted">Total Students</span>
                        </div>
                        <div>
                            <span class="block font-bold text-xl text-ink">{{ assignments.length }}</span>
                            <span class="text-ink-muted">Assignments</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tabs -->
            <div class="border-b border-border-light">
                <div class="flex gap-6">
                    <button @click="activeTab = 'classes'" class="pb-3 text-sm font-medium transition-all relative"
                        :class="activeTab === 'classes' ? 'text-primary' : 'text-ink-muted hover:text-ink'">
                        Classes
                        <div v-if="activeTab === 'classes'"
                            class="absolute bottom-0 left-0 w-full h-0.5 bg-primary rounded-t-full"></div>
                    </button>
                    <button @click="activeTab = 'assignments'" class="pb-3 text-sm font-medium transition-all relative"
                        :class="activeTab === 'assignments' ? 'text-primary' : 'text-ink-muted hover:text-ink'">
                        Assignments
                        <div v-if="activeTab === 'assignments'"
                            class="absolute bottom-0 left-0 w-full h-0.5 bg-primary rounded-t-full"></div>
                    </button>
                </div>
            </div>

            <!-- Classes Tab -->
            <div v-if="activeTab === 'classes'" class="animate-fade-in">
                <div class="grid gap-4">
                    <div v-for="section in sections" :key="section.section_id"
                        class="bg-surface border border-border-light rounded-xl p-5 shadow-sm hover:shadow-card transition-all">
                        <div class="flex justify-between items-start">
                            <div>
                                <div class="flex items-center gap-2 mb-1">
                                    <span
                                        class="px-2 py-0.5 rounded text-[0.65rem] font-bold uppercase tracking-wider bg-primary/10 text-primary">
                                        {{ section.course?.course_code }}
                                    </span>
                                    <span class="text-xs text-ink-muted">{{ section.term?.term_name }}</span>
                                </div>
                                <h3 class="text-lg font-semibold text-ink">{{ section.course?.course_name }}</h3>
                                <p class="text-sm text-ink-muted mt-1">
                                    <Icons name="mdi-door" class="inline text-xs mr-1" /> {{ section.room?.room_number
                                        || 'TBA' }}
                                    <span class="mx-2">·</span>
                                    <Icons name="mdi-clock-outline" class="inline text-xs mr-1" /> {{
                                        section.schedule_pattern }}
                                </p>
                            </div>
                            <div class="text-right">
                                <span class="block text-xl font-bold text-ink">{{ section.enrolled_count }}</span>
                                <span class="text-xs text-ink-muted">Students</span>
                            </div>
                        </div>
                    </div>
                    <div v-if="sections.length === 0"
                        class="text-center py-8 text-ink-muted bg-surface rounded-xl border border-border-light border-dashed">
                        <p>No classes found.</p>
                    </div>
                </div>
            </div>

            <!-- Assignments Tab -->
            <div v-if="activeTab === 'assignments'" class="animate-fade-in">
                <div class="grid gap-4">
                    <div v-for="asn in assignments" :key="asn.assignment_id"
                        class="bg-surface border border-border-light rounded-xl p-5 shadow-sm hover:shadow-card transition-all">
                        <div class="flex justify-between items-start">
                            <div>
                                <div class="flex items-center gap-2 mb-1">
                                    <span
                                        class="px-2 py-0.5 rounded text-[0.65rem] font-bold uppercase tracking-wider bg-coral/10 text-coral">
                                        {{ asn.course_code }}
                                    </span>
                                    <span class="text-xs text-ink-muted" v-if="asn.section_number">Sec {{
                                        asn.section_number }}</span>
                                </div>
                                <h3 class="text-lg font-semibold text-ink">{{ asn.assignment_name }}</h3>
                                <p class="text-xs text-ink-muted mt-2">
                                    Due: {{ new Date(asn.due_date).toLocaleDateString() }}
                                </p>
                            </div>
                            <div>
                                <span v-if="asn.is_published"
                                    class="px-2 py-1 rounded-full text-xs font-semibold bg-success/10 text-success">Published</span>
                                <span v-else
                                    class="px-2 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-500">Draft</span>
                            </div>
                        </div>
                    </div>
                    <div v-if="assignments.length === 0"
                        class="text-center py-8 text-ink-muted bg-surface rounded-xl border border-border-light border-dashed">
                        <p>No assignments found.</p>
                    </div>
                </div>
            </div>

        </div>
    </div>
</template>
