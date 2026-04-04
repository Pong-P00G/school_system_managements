<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useAuthStore } from '../../stores/auth'
import {
    getFacultySections,
    getSectionEnrollments,
    getStudents,
    enrollStudent,
    getSectionAssignments,
    getAssignmentTeams,
    createAssignmentTeam,
    addTeamMember,
    removeTeamMember
} from '../../services/api.js'
import Icons from '../../components/icon/Icons.vue'

const authStore = useAuthStore()
const loading = ref(true)
const sections = ref([])
const selectedSectionId = ref(null)
const activeTab = ref('enrollment') // enrollment, teams

// Enrollment State
const enrolledStudents = ref([])
const showEnrollModal = ref(false)
const studentSearchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const enrolling = ref(false)

// Team State
const assignments = ref([])
const selectedAssignmentId = ref(null)
const teams = ref([])
const showCreateTeamModal = ref(false)
const newTeamName = ref('')
const creatingTeam = ref(false)
const showAddMemberModal = ref(false)
const selectedTeamId = ref(null)
const addingMember = ref(false)

onMounted(async () => {
    if (!authStore.user?.user_id) return
    try {
        const res = await getFacultySections('me')
        sections.value = res.data.sections || []
        if (sections.value.length > 0) {
            selectedSectionId.value = sections.value[0].section_id
        }
    } catch (e) {
        console.error("Error fetching sections", e)
    } finally {
        loading.value = false
    }
})

watch(selectedSectionId, async (newId) => {
    if (!newId) return
    await fetchEnrollments()
    if (activeTab.value === 'teams') {
        await fetchAssignments()
    }
})

watch(activeTab, async (newTab) => {
    if (newTab === 'teams' && selectedSectionId.value) {
        await fetchAssignments()
    }
})

watch(selectedAssignmentId, async (newId) => {
    if (newId) {
        await fetchTeams()
    } else {
        teams.value = []
    }
})

// --- Enrollment Logic ---
const fetchEnrollments = async () => {
    if (!selectedSectionId.value) return
    loading.value = true
    try {
        const res = await getSectionEnrollments(selectedSectionId.value)
        enrolledStudents.value = res.data.enrollments || []
    } catch (e) { console.error(e) }
    finally { loading.value = false }
}

const searchStudents = async () => {
    if (!studentSearchQuery.value) return
    searching.value = true
    try {
        const res = await getStudents(0, 50, null, null, null, studentSearchQuery.value)
        // Filter out already enrolled
        const enrolledIds = new Set(enrolledStudents.value.map(e => e.student_id))
        searchResults.value = res.data.students.filter(s => !enrolledIds.has(s.student_id))
    } catch (e) { console.error(e) }
    finally { searching.value = false }
}

const handleEnroll = async (student) => {
    if (!confirm(`Enroll ${student.user.personal_info.first_name} ${student.user.personal_info.last_name}?`)) return
    enrolling.value = true
    try {
        await enrollStudent(selectedSectionId.value, student.student_id)
        showEnrollModal.value = false
        studentSearchQuery.value = ''
        searchResults.value = []
        await fetchEnrollments()
    } catch (e) {
        alert("Failed to enroll: " + (e.response?.data?.detail || e.message))
    } finally {
        enrolling.value = false
    }
}

// --- Team Logic ---
const fetchAssignments = async () => {
    if (!selectedSectionId.value) return
    try {
        const res = await getSectionAssignments(selectedSectionId.value)
        assignments.value = res.data.assignments || []
        if (assignments.value.length > 0 && !selectedAssignmentId.value) {
            selectedAssignmentId.value = assignments.value[0].assignment_id
        }
    } catch (e) { console.error(e) }
}

const fetchTeams = async () => {
    if (!selectedAssignmentId.value) return
    try {
        const res = await getAssignmentTeams(selectedAssignmentId.value)
        teams.value = res.data || []
    } catch (e) { console.error(e) }
}

const handleCreateTeam = async () => {
    if (!newTeamName.value) return
    creatingTeam.value = true
    try {
        await createAssignmentTeam(selectedAssignmentId.value, newTeamName.value)
        showCreateTeamModal.value = false
        newTeamName.value = ''
        await fetchTeams()
    } catch (e) {
        alert("Failed to create team: " + (e.response?.data?.detail || e.message))
    } finally {
        creatingTeam.value = false
    }
}

const openAddMember = (teamId) => {
    selectedTeamId.value = teamId
    showAddMemberModal.value = true
}

const handleAddMember = async (studentId) => {
    addingMember.value = true
    try {
        await addTeamMember(selectedTeamId.value, studentId)
        showAddMemberModal.value = false
        await fetchTeams()
    } catch (e) {
        alert("Failed to add member: " + (e.response?.data?.detail || e.message))
    } finally {
        addingMember.value = false
    }
}

const handleRemoveMember = async (teamId, studentId) => {
    if (!confirm("Remove student from team?")) return
    try {
        await removeTeamMember(teamId, studentId)
        await fetchTeams()
    } catch (e) {
        alert("Failed to remove member: " + (e.response?.data?.detail || e.message))
    }
}

// Computed for Add Member Modal
const availableStudentsForTeam = computed(() => {
    if (!teams.value) return enrolledStudents.value

    const assignedStudentIds = new Set()
    teams.value.forEach(t => {
        t.members.forEach(m => assignedStudentIds.add(m.student_id))
    })

    return enrolledStudents.value.filter(e => !assignedStudentIds.has(e.student_id))
})

</script>

<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
                <h1 class="text-2xl font-bold text-ink tracking-tight">Class Management</h1>
                <p class="text-sm text-ink-muted mt-0.5">Manage enrollments and assignment teams</p>
            </div>
            <div
                class="flex items-center gap-2 bg-surface border border-border-light rounded-xl shadow-card pl-3 pr-1 py-1">
                <Icons name="mdi-filter-variant" class="text-ink-muted text-lg" />
                <select v-model="selectedSectionId"
                    class="border-none bg-transparent text-sm text-ink font-sans py-2 pr-8 focus:outline-none cursor-pointer">
                    <option v-for="section in sections" :key="section.section_id" :value="section.section_id">
                        {{ section.course?.course_code }} — Sec {{ section.section_number }}
                    </option>
                </select>
            </div>
        </div>

        <!-- Tabs -->
        <div class="border-b border-border-light">
            <div class="flex gap-6">
                <button @click="activeTab = 'enrollment'" class="pb-3 text-sm font-medium transition-all relative"
                    :class="activeTab === 'enrollment' ? 'text-primary' : 'text-ink-muted hover:text-ink'">
                    Enrollment
                    <div v-if="activeTab === 'enrollment'"
                        class="absolute bottom-0 left-0 w-full h-0.5 bg-primary rounded-t-full"></div>
                </button>
                <button @click="activeTab = 'teams'" class="pb-3 text-sm font-medium transition-all relative"
                    :class="activeTab === 'teams' ? 'text-primary' : 'text-ink-muted hover:text-ink'">
                    Assignment Teams
                    <div v-if="activeTab === 'teams'"
                        class="absolute bottom-0 left-0 w-full h-0.5 bg-primary rounded-t-full"></div>
                </button>
            </div>
        </div>

        <!-- Enrollment Tab -->
        <div v-if="activeTab === 'enrollment'" class="animate-fade-in">
            <div class="flex justify-end mb-4">
                <button @click="showEnrollModal = true"
                    class="bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-hover flex items-center gap-2 transition-all shadow-lg shadow-primary/25">
                    <Icons name="mdi-plus" /> Enroll Student
                </button>
            </div>

            <div class="bg-surface border border-border-light rounded-2xl shadow-card overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="w-full border-collapse" style="min-width: 500px;">
                        <thead class="bg-page">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-semibold text-ink-muted uppercase">Student
                                </th>
                                <th class="px-6 py-3 text-left text-xs font-semibold text-ink-muted uppercase">ID</th>
                                <th class="px-6 py-3 text-left text-xs font-semibold text-ink-muted uppercase">Status
                                </th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100">
                            <tr v-for="enr in enrolledStudents" :key="enr.enrollment_id" class="hover:bg-slate-50">
                                <td class="px-6 py-4">
                                    <div class="font-medium text-ink">{{ enr.student?.user?.personal_info?.first_name }}
                                        {{
                                            enr.student?.user?.personal_info?.last_name }}</div>
                                    <div class="text-xs text-ink-muted">{{ enr.student?.user?.email }}</div>
                                </td>
                                <td class="px-6 py-4 text-sm text-ink-muted">{{ enr.student?.student_number }}</td>
                                <td class="px-6 py-4">
                                    <span
                                        class="px-2 py-1 rounded-full text-xs font-medium bg-success/10 text-success capitalize">{{
                                            enr.enrollment_status }}</span>
                                </td>
                            </tr>
                            <tr v-if="enrolledStudents.length === 0">
                                <td colspan="3" class="px-6 py-8 text-center text-ink-muted">No students enrolled yet.
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Teams Tab -->
        <div v-if="activeTab === 'teams'" class="animate-fade-in space-y-4">
            <div class="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4 mb-4">
                <label class="text-sm font-medium text-ink">Assignment:</label>
                <select v-model="selectedAssignmentId"
                    class="border border-border-light rounded-lg px-3 py-2 text-sm bg-surface text-ink focus:border-primary focus:outline-none min-w-50">
                    <option v-for="asn in assignments" :key="asn.assignment_id" :value="asn.assignment_id">
                        {{ asn.assignment_name }}
                    </option>
                </select>
                <button @click="showCreateTeamModal = true"
                    class="ml-auto bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-hover flex items-center gap-2 shadow-lg shadow-primary/25">
                    <Icons name="mdi-plus" /> New Team
                </button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div v-for="team in teams" :key="team.team_id"
                    class="bg-surface border border-border-light rounded-2xl shadow-sm p-4 hover:shadow-card transition-all">
                    <div class="flex justify-between items-center mb-3">
                        <h3 class="font-bold text-ink">{{ team.name }}</h3>
                        <button @click="openAddMember(team.team_id)"
                            class="text-xs text-primary font-medium hover:underline">+ Add Member</button>
                    </div>
                    <div class="space-y-2">
                        <div v-for="member in team.members" :key="member.student_id"
                            class="flex justify-between items-center text-sm bg-slate-50 p-2 rounded-lg border border-slate-100">
                            <span class="text-ink truncate">{{ member.name }}</span>
                            <button @click="handleRemoveMember(team.team_id, member.student_id)"
                                class="text-red-500 hover:text-red-700 ml-2">
                                <Icons name="mdi-close" class="w-4 h-4" />
                            </button>
                        </div>
                        <div v-if="team.members.length === 0" class="text-xs text-ink-muted italic py-2 text-center">No
                            members yet</div>
                    </div>
                </div>
                <div v-if="teams.length === 0"
                    class="col-span-full text-center py-12 text-ink-muted bg-surface rounded-2xl border border-dashed border-border-light">
                    <p>No teams created for this assignment.</p>
                </div>
            </div>
        </div>

        <!-- Enroll Modal -->
        <div v-if="showEnrollModal"
            class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
            <div class="bg-surface rounded-2xl shadow-xl w-full max-w-md p-6 animate-fade-in-up">
                <h2 class="text-xl font-bold text-ink mb-4">Enroll Student</h2>
                <div class="flex gap-2 mb-4">
                    <input v-model="studentSearchQuery" @keyup.enter="searchStudents"
                        placeholder="Search by name or number..."
                        class="flex-1 border border-border-light rounded-lg px-3 py-2 text-sm focus:border-primary focus:outline-none" />
                    <button @click="searchStudents"
                        class="bg-slate-100 text-ink-medium px-4 py-2 rounded-lg hover:bg-slate-200">
                        <Icons name="mdi-magnify" />
                    </button>
                </div>

                <div class="max-h-60 overflow-y-auto custom-scrollbar space-y-2 mb-4">
                    <div v-if="searching" class="text-center py-4 text-ink-muted">Searching...</div>
                    <div v-else-if="searchResults.length === 0 && studentSearchQuery"
                        class="text-center py-4 text-ink-muted">No students found.</div>

                    <div v-for="student in searchResults" :key="student.student_id"
                        class="flex justify-between items-center p-3 border border-border-light rounded-lg hover:bg-slate-50 cursor-pointer"
                        @click="handleEnroll(student)">
                        <div>
                            <div class="font-medium text-ink text-sm">{{ student.user.personal_info.first_name }} {{
                                student.user.personal_info.last_name }}</div>
                            <div class="text-xs text-ink-muted">{{ student.student_number }}</div>
                        </div>
                        <Icons name="mdi-plus" class="text-primary" />
                    </div>
                </div>

                <div class="flex justify-end">
                    <button @click="showEnrollModal = false"
                        class="text-ink-muted hover:text-ink font-medium text-sm">Close</button>
                </div>
            </div>
        </div>

        <!-- Create Team Modal -->
        <div v-if="showCreateTeamModal"
            class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
            <div class="bg-surface rounded-2xl shadow-xl w-full max-w-md p-6 animate-fade-in-up">
                <h2 class="text-xl font-bold text-ink mb-4">Create Assignment Team</h2>
                <div class="mb-4">
                    <label class="block text-sm font-medium text-ink mb-1">Team Name</label>
                    <input v-model="newTeamName"
                        class="w-full border border-border-light rounded-lg px-3 py-2 text-sm focus:border-primary focus:outline-none"
                        placeholder="e.g. Team Alpha" />
                </div>
                <div class="flex justify-end gap-3">
                    <button @click="showCreateTeamModal = false"
                        class="text-ink-muted hover:text-ink font-medium text-sm">Cancel</button>
                    <button @click="handleCreateTeam" :disabled="creatingTeam || !newTeamName"
                        class="bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-hover disabled:opacity-50">Create</button>
                </div>
            </div>
        </div>

        <!-- Add Member Modal -->
        <div v-if="showAddMemberModal"
            class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
            <div class="bg-surface rounded-2xl shadow-xl w-full max-w-md p-6 animate-fade-in-up">
                <h2 class="text-xl font-bold text-ink mb-4">Add Student to Team</h2>
                <div class="max-h-60 overflow-y-auto custom-scrollbar space-y-2 mb-4">
                    <div v-if="availableStudentsForTeam.length === 0" class="text-center py-4 text-ink-muted">All
                        students are already assigned or no students available.</div>
                    <div v-for="student in availableStudentsForTeam" :key="student.student_id"
                        class="flex justify-between items-center p-3 border border-border-light rounded-lg hover:bg-slate-50 cursor-pointer"
                        @click="handleAddMember(student.student_id)">
                        <div>
                            <div class="font-medium text-ink text-sm">{{
                                student.student?.user?.personal_info?.first_name }} {{
                                    student.student?.user?.personal_info?.last_name }}</div>
                            <div class="text-xs text-ink-muted">{{ student.student?.student_number }}</div>
                        </div>
                        <Icons name="mdi-plus" class="text-primary" />
                    </div>
                </div>
                <div class="flex justify-end">
                    <button @click="showAddMemberModal = false"
                        class="text-ink-muted hover:text-ink font-medium text-sm">Close</button>
                </div>
            </div>
        </div>

    </div>
</template>
