
<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  getFacultySections, getSectionAssignments, getSectionEnrollments, updateEnrollment,
  createAssignment, updateAssignment, deleteAssignment
} from '../../services/api.js'
import { useAuthStore } from '../../stores/auth'
import Icons from '../../components/icon/Icons.vue'
import { useToast } from '../../composables/useToast'

const toast = useToast()
const route = useRoute()
const authStore = useAuthStore()
const loading = ref(true)
const sections = ref([])
const selectedSectionId = ref(route.query.sectionId ? parseInt(route.query.sectionId) : null)
const assignments = ref([])
const enrollments = ref([])
const gradingLoading = ref(false)

const showAssignmentModal = ref(false)
const modalMode = ref('create')
const assignmentForm = ref({
  assignment_id: null, assignment_name: '', assignment_type: 'Homework',
  max_points: 100, weight_percentage: 10, due_date: '', description: '', is_published: true
})

const fetchData = async () => {
  if (!authStore.user?.user_id) return
  loading.value = true
  try {
    const secRes = await getFacultySections('me')
    sections.value = secRes.data.sections || []
    if (sections.value.length > 0 && !selectedSectionId.value) selectedSectionId.value = sections.value[0].section_id
    if (selectedSectionId.value) await fetchSectionDetails(selectedSectionId.value)
  } catch (error) { console.error('Error fetching grading data:', error) }
  finally { loading.value = false }
}

const fetchSectionDetails = async (sectionId) => {
  try {
    const [asnRes, enrRes] = await Promise.all([getSectionAssignments(sectionId), getSectionEnrollments(sectionId)])
    assignments.value = asnRes.data.assignments || []
    enrollments.value = enrRes.data.enrollments || []
  } catch (error) { console.error('Error fetching section details:', error) }
}

watch(selectedSectionId, (newId) => { if (newId) fetchSectionDetails(newId) })
onMounted(fetchData)

const handleGradeUpdate = async (enr, field) => {
  gradingLoading.value = true
  try {
    await updateEnrollment(enr.enrollment_id, { [field]: enr[field], enrollment_status: field === 'grade' || field === 'final_grade' ? 'completed' : 'enrolled' })
    toast.success('Grade saved')
  } catch (error) { toast.error('Failed to save grade.') }
  finally { gradingLoading.value = false }
}

const openAssignmentModal = (mode, asn = null) => {
  modalMode.value = mode
  if (mode === 'edit' && asn) {
    assignmentForm.value = { ...asn, due_date: asn.due_date ? new Date(asn.due_date).toISOString().slice(0, 16) : '' }
  } else {
    assignmentForm.value = { assignment_id: null, section_id: selectedSectionId.value, assignment_name: '', assignment_type: 'Homework', max_points: 100, weight_percentage: 10, due_date: '', description: '', is_published: true }
  }
  showAssignmentModal.value = true
}

const handleSaveAssignment = async () => {
  try {
    const payload = { ...assignmentForm.value }
    if (!payload.due_date) payload.due_date = null
    if (modalMode.value === 'create') { await createAssignment(payload); toast.success('Assignment created') }
    else { await updateAssignment(payload.assignment_id, payload); toast.success('Assignment updated') }
    showAssignmentModal.value = false
    await fetchSectionDetails(selectedSectionId.value)
  } catch (error) { toast.error('Failed to save assignment.') }
}

const handleDeleteAssignment = async (asnId) => {
  if (!confirm('Delete this assignment?')) return
  try { await deleteAssignment(asnId); toast.success('Assignment deleted'); await fetchSectionDetails(selectedSectionId.value) }
  catch (error) { toast.error('Failed to delete assignment.') }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
      <div>
        <h1 class="text-2xl font-bold text-ink tracking-tight">Grade Management</h1>
        <p class="text-sm text-ink-muted mt-0.5">Manage assignments and enter student grades</p>
      </div>
      <div class="flex items-center gap-2 bg-surface border border-border-light rounded-xl shadow-card pl-3 pr-1 py-1">
        <Icons name="mdi-book-search" class="text-ink-muted text-lg" />
        <select v-model="selectedSectionId"
          class="border-none bg-transparent text-sm text-ink font-sans py-2 pr-8 focus:outline-none cursor-pointer">
          <option v-for="section in sections" :key="section.section_id" :value="section.section_id">
            {{ section.course?.course_code }} — Sec {{ section.section_number }}
          </option>
        </select>
      </div>
    </div>

    <!-- Assignments Table -->
    <div class="bg-surface border border-border-light rounded-2xl shadow-card animate-fade-in">
      <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-full bg-coral/12 text-coral flex items-center justify-center text-sm">
            <Icons name="mdi-clipboard-text-outline" />
          </div>
          <h3 class="text-base font-semibold text-ink">Assignments</h3>
        </div>
        <button @click="openAssignmentModal('create')"
          class="inline-flex items-center gap-1.5 px-4 py-2 bg-coral text-white border-none rounded-xl font-sans text-xs font-medium cursor-pointer transition-all hover:bg-coral-hover hover:shadow-[0_4px_12px_rgba(224,122,95,0.3)]">
          <Icons name="mdi-plus" /> New Assignment
        </button>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full border-collapse">
          <thead class="bg-page">
            <tr>
              <th
                class="px-6 py-3.5 text-left text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Name</th>
              <th
                class="px-6 py-3.5 text-left text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Type</th>
              <th
                class="px-6 py-3.5 text-center text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Weight</th>
              <th
                class="px-6 py-3.5 text-center text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Submissions</th>
              <th
                class="px-6 py-3.5 text-left text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Due Date</th>
              <th
                class="px-6 py-3.5 text-right text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="6" class="px-6 py-6 text-center text-ink-muted italic">Finding assignments...</td>
            </tr>
            <tr v-else-if="assignments.length === 0">
              <td colspan="6" class="px-6 py-8 text-center text-ink-muted">No assignments created yet.</td>
            </tr>
            <tr v-for="asn in assignments" :key="asn.assignment_id"
              class="border-b border-border-light last:border-b-0 hover:bg-primary transition-colors">
              <td class="px-6 py-3.5 text-sm font-medium text-ink">{{ asn.assignment_name }}</td>
              <td class="px-6 py-3.5"><span
                  class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-sage/15 text-[#5e6e5f]">{{
                    asn.assignment_type }}</span></td>
              <td class="px-6 py-3.5 text-sm text-center text-ink">{{ asn.weight_percentage || 0 }}%</td>
              <td class="px-6 py-3.5 text-center"><span
                  class="px-2 py-0.5 rounded-full text-xs font-medium bg-info/12 text-info">{{ asn.submissions?.length
                  || 0 }}</span></td>
              <td class="px-6 py-3.5 text-sm text-ink-muted">{{ asn.due_date ? new
                Date(asn.due_date).toLocaleDateString() : 'No date' }}</td>
              <td class="px-6 py-3.5 text-right">
                <div class="flex justify-end gap-1">
                  <button @click="openAssignmentModal('edit', asn)"
                    class="w-8 h-8 rounded-lg bg-transparent border-none text-ink-muted text-base flex items-center justify-center cursor-pointer transition-all hover:bg-info hover:text-info">
                    <Icons name="mdi-pencil" />
                  </button>
                  <button @click="handleDeleteAssignment(asn.assignment_id)"
                    class="w-8 h-8 rounded-lg bg-transparent border-none text-ink-muted text-base flex items-center justify-center cursor-pointer transition-all hover:bg-error hover:text-error">
                    <Icons name="mdi-delete" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Student Grades -->
    <div class="bg-surface border border-border-light rounded-2xl shadow-card animate-fade-in delay-2">
      <div class="flex items-center gap-2 px-6 py-4 border-b border-border-light">
        <div class="w-7 h-7 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm">
          <Icons name="mdi-account-star-outline" />
        </div>
        <h3 class="text-base font-semibold text-ink">Student Performance & Final Grades</h3>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full border-collapse">
          <thead class="bg-page">
            <tr>
              <th
                class="px-6 py-3.5 text-left text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Student</th>
              <th
                class="px-6 py-3.5 text-center text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Attendance</th>
              <th
                class="px-6 py-3.5 text-center text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Midterm</th>
              <th
                class="px-6 py-3.5 text-center text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Final Grade</th>
              <th
                class="px-6 py-3.5 text-right text-[0.7rem] font-semibold text-ink-muted uppercase tracking-wider border-b border-border-light">
                Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="5" class="px-6 py-6 text-center text-ink-muted italic">Gathering student data...</td>
            </tr>
            <tr v-for="enr in enrollments" :key="enr.enrollment_id"
              class="border-b border-border-light last:border-b-0 hover:bg-primary transition-colors">
              <td class="px-6 py-3.5">
                <div class="flex items-center">
                  <div
                    class="w-8 h-8 rounded-full bg-primary/10 text-primary text-xs font-semibold flex items-center justify-center shrink-0">
                    {{ enr.student?.user?.personal_info?.first_name?.[0] }}{{
                      enr.student?.user?.personal_info?.last_name?.[0] }}
                  </div>
                  <div class="ml-3">
                    <p class="font-medium text-sm text-ink">{{ enr.student?.user?.personal_info?.first_name }} {{
                      enr.student?.user?.personal_info?.last_name }}</p>
                    <p class="text-[0.7rem] text-ink-muted font-mono">{{ enr.student?.student_number }}</p>
                  </div>
                </div>
              </td>
              <td class="px-6 py-3.5 text-center">
                <input type="number" v-model.number="enr.attendance_percentage"
                  @change="handleGradeUpdate(enr, 'attendance_percentage')"
                  class="w-16 h-8 text-center text-sm border-[1.5px] border-border-medium rounded-lg bg-surface text-ink font-sans p-0 transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.1)]"
                  placeholder="%">
              </td>
              <td class="px-6 py-3.5 text-center">
                <input type="text" v-model="enr.midterm_grade" @change="handleGradeUpdate(enr, 'midterm_grade')"
                  class="w-12 h-8 text-center text-sm border-[1.5px] border-border-medium rounded-lg bg-surface text-ink font-sans p-0 transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.1)]"
                  placeholder="A">
              </td>
              <td class="px-6 py-3.5 text-center">
                <input type="text" v-model="enr.grade" @change="handleGradeUpdate(enr, 'grade')"
                  class="w-12 h-8 text-center text-sm font-bold border-[1.5px] border-ink-muted rounded-lg bg-surface text-ink font-sans p-0 transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.1)]"
                  placeholder="A">
              </td>
              <td class="px-6 py-3.5 text-right">
                <span :class="[
                  'px-2 py-0.5 rounded-full text-[0.65rem] font-medium uppercase tracking-wider',
                  enr.enrollment_status === 'completed' ? 'bg-success/12 text-[#047857]' : 'bg-warning/12 text-[#b45309]'
                ]">{{ enr.enrollment_status }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Assignment Modal -->
    <div v-if="showAssignmentModal"
      class="fixed inset-0 bg-ink/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="showAssignmentModal = false">
      <div class="bg-surface rounded-2xl shadow-modal w-full max-w-130 overflow-hidden animate-fade-in">
        <div class="flex items-center justify-between px-6 py-5 border-b border-border-light bg-page">
          <h3 class="text-lg font-semibold text-ink m-0">{{ modalMode === 'create' ? 'Create Assignment' : 'Edit Assignment' }}</h3>
          <button @click="showAssignmentModal = false"
            class="w-8 h-8 rounded-lg bg-transparent border-none text-ink-muted text-base flex items-center justify-center cursor-pointer hover:bg-primary">
            <Icons name="mdi-close" />
          </button>
        </div>
        <form @submit.prevent="handleSaveAssignment" class="p-6 space-y-4">
          <div>
            <label class="block text-xs font-medium text-ink-secondary mb-1.5">Assignment Name</label>
            <input v-model="assignmentForm.assignment_name" type="text" required
              class="w-full px-3.5 py-2.5 text-sm font-sans border-[1.5px] border-border-medium rounded-xl bg-surface text-ink transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.12)]" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-ink-secondary mb-1.5">Type</label>
              <select v-model="assignmentForm.assignment_type"
                class="w-full px-3.5 py-2.5 text-sm font-sans border-[1.5px] border-border-medium rounded-xl bg-surface text-ink transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.12)]">
                <option>Homework</option>
                <option>Quiz</option>
                <option>Midterm</option>
                <option>Final</option>
                <option>Project</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-ink-secondary mb-1.5">Due Date</label>
              <input v-model="assignmentForm.due_date" type="datetime-local" required
                class="w-full px-3.5 py-2.5 text-sm font-sans border-[1.5px] border-border-medium rounded-xl bg-surface text-ink transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.12)]" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-ink-secondary mb-1.5">Max Points</label>
              <input v-model.number="assignmentForm.max_points" type="number" step="0.5" required
                class="w-full px-3.5 py-2.5 text-sm font-sans border-[1.5px] border-border-medium rounded-xl bg-surface text-ink transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.12)]" />
            </div>
            <div>
              <label class="block text-xs font-medium text-ink-secondary mb-1.5">Weight (%)</label>
              <input v-model.number="assignmentForm.weight_percentage" type="number" step="0.1" required
                class="w-full px-3.5 py-2.5 text-sm font-sans border-[1.5px] border-border-medium rounded-xl bg-surface text-ink transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.12)]" />
            </div>
          </div>
          <div>
            <label class="block text-xs font-medium text-ink-secondary mb-1.5">Description</label>
            <textarea v-model="assignmentForm.description" rows="3"
              class="w-full px-3.5 py-2.5 text-sm font-sans border-[1.5px] border-border-medium rounded-xl bg-surface text-ink transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.12)]"></textarea>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="assignmentForm.is_published" type="checkbox" id="publish"
              class="w-4 h-4 accent-primary cursor-pointer">
            <label for="publish" class="text-sm text-ink-secondary">Publish immediately</label>
          </div>
        </form>
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-border-light bg-page">
          <button type="button" @click="showAssignmentModal = false"
            class="inline-flex items-center px-4 py-2 bg-transparent text-primary border-[1.5px] border-border-medium rounded-xl font-sans text-sm font-medium cursor-pointer transition-all hover:border-primary hover:bg-primary">Cancel</button>
          <button @click="handleSaveAssignment"
            class="inline-flex items-center px-5 py-2 bg-coral text-white border-none rounded-xl font-sans text-sm font-medium cursor-pointer transition-all hover:bg-coral-hover hover:shadow-[0_4px_12px_rgba(224,122,95,0.3)]">{{
              modalMode === 'create' ? 'Create' : 'Save Changes' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>