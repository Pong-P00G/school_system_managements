<script setup>
import { ref, onMounted } from 'vue'
import { getMyEnrollments, getMyStudentProfile, getSections, createEnrollment, joinSectionByCode } from '../../services/api.js'
import { useAuthStore } from '../../stores/auth'
import { useToast } from '../../composables/useToast'
import Icons from '../../components/icon/Icons.vue'

const toast = useToast()
const authStore = useAuthStore()
const loading = ref(true)
const enrollments = ref([])
const availableSections = ref([])
const studentProfile = ref(null)
const noStudentProfile = ref(false)

// Join by code
const joinCode = ref('')
const joinLoading = ref(false)

const fetchPageData = async () => {
  loading.value = true
  try {
    // First get student profile to have the proper student_id
    const profileRes = await getMyStudentProfile()
    studentProfile.value = profileRes.data
  } catch (err) {
    // If no student profile linked, show a message but don't crash
    noStudentProfile.value = true
    loading.value = false
    return
  }

  try {
    const [enrRes, secRes] = await Promise.all([
      getMyEnrollments(),
      getSections(0, 50)
    ])
    enrollments.value = enrRes.data.enrollments || []
    const enrolledSectionIds = new Set(enrollments.value.map(e => e.section_id))
    availableSections.value = (secRes.data.sections || []).filter(s => !enrolledSectionIds.has(s.section_id))
  } catch (error) {
    console.error('Error fetching courses:', error)
  } finally {
    loading.value = false
  }
}

const handleEnroll = async (sectionId) => {
  if (!studentProfile.value) return
  try {
    await createEnrollment({
      student_id: studentProfile.value.student_id,
      section_id: sectionId,
      enrollment_status: 'enrolled'
    })
    toast.success('Successfully enrolled in course!')
    await fetchPageData()
  } catch (error) {
    toast.error(error.response?.data?.detail || 'Failed to enroll in course.')
  }
}

const handleJoinByCode = async () => {
  if (!joinCode.value.trim() || !studentProfile.value) return
  joinLoading.value = true
  try {
    const res = await joinSectionByCode(joinCode.value.trim(), studentProfile.value.student_id)
    toast.success(res.data.message || 'Successfully joined the class!')
    joinCode.value = ''
    await fetchPageData()
  } catch (error) {
    toast.error(error.response?.data?.detail || 'Failed to join class. Check the code and try again.')
  } finally {
    joinLoading.value = false
  }
}

onMounted(fetchPageData)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
      <div>
        <h1 class="text-2xl font-bold text-ink tracking-tight">Course Registration</h1>
        <p class="text-sm text-ink-muted mt-0.5">Manage your enrollments and discover new courses</p>
      </div>
    </div>

    <!-- No Student Profile Warning -->
    <div v-if="noStudentProfile"
      class="bg-surface border border-border-light rounded-2xl shadow-card p-8 text-center animate-fade-in">
      <Icons name="mdi-account-alert" class="w-12 h-12 text-coral mb-3" />
      <h3 class="text-lg font-semibold text-ink mb-1">No Student Profile Found</h3>
      <p class="text-sm text-ink-muted">Your account is not linked to a student profile. Please contact the
        administrator to set up your student record.</p>
    </div>

    <template v-else>
      <!-- Join by Code Card -->
      <div class="bg-surface border border-border-light rounded-2xl shadow-card animate-fade-in p-5 sm:p-6">
        <div class="flex items-center gap-2 mb-3">
          <div class="w-7 h-7 rounded-full bg-coral/12 text-coral flex items-center justify-center text-sm">
            <Icons name="mdi-key-variant" />
          </div>
          <h3 class="text-base font-semibold text-ink">Join a Class with Code</h3>
        </div>
        <p class="text-sm text-ink-muted mb-4">Enter the 6-character class code shared by your instructor to join a
          class.
        </p>
        <div class="flex flex-col sm:flex-row gap-3">
          <input v-model="joinCode" type="text" placeholder="e.g. ABC123" maxlength="6" @keyup.enter="handleJoinByCode"
            class="flex-1 px-4 py-2.5 text-sm font-sans border-[1.5px] border-border-medium rounded-xl bg-surface text-ink tracking-[0.15em] font-bold uppercase transition-all focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(47,79,79,0.12)]" />
          <button @click="handleJoinByCode" :disabled="!joinCode.trim() || joinLoading"
            class="inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-coral text-white border-none rounded-xl font-sans text-sm font-medium cursor-pointer transition-all duration-200 hover:bg-coral-hover hover:shadow-[0_4px_12px_rgba(224,122,95,0.3)] disabled:opacity-50 disabled:cursor-not-allowed">
            <Icons v-if="joinLoading" name="mdi-loading" class="animate-spin" />
            <Icons v-else name="mdi-login" />
            {{ joinLoading ? 'Joining...' : 'Join Class' }}
          </button>
        </div>
      </div>

      <!-- Enrolled Courses -->
      <div class="bg-surface border border-border-light rounded-2xl shadow-card animate-fade-in delay-2">
        <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
          <div class="flex items-center gap-2">
            <div class="w-7 h-7 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm">
              <Icons name="mdi-book-open-variant" />
            </div>
            <h3 class="text-base font-semibold text-ink">My Current Enrollments</h3>
          </div>
          <span class="px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">{{ enrollments.length }}
            courses</span>
        </div>
        <div>
          <div v-if="loading" class="text-center py-8 text-ink-muted">
            <Icons name="mdi-loading" class="animate-spin w-6 h-6 mb-2" />
            <p>Loading...</p>
          </div>
          <div v-else-if="enrollments.length === 0" class="text-center py-10 text-ink-muted">
            <Icons name="mdi-book-off-outline" class="w-10 h-10 mb-2" />
            <p>You are not enrolled in any courses yet.</p>
          </div>
          <div v-else>
            <div v-for="enr in enrollments" :key="enr.enrollment_id"
              class="flex flex-col sm:flex-row sm:items-center justify-between px-4 sm:px-6 py-4 border-b border-border-light last:border-b-0 hover:bg-primary/2.5 transition-colors gap-2 sm:gap-0">
              <div class="flex items-center gap-3">
                <div
                  class="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center text-lg shrink-0">
                  <Icons name="mdi-book-open-variant" />
                </div>
                <div>
                  <p class="font-medium text-sm text-ink">{{ enr.section?.course?.course_code }} — {{
                    enr.section?.course?.course_name }}</p>
                  <p class="text-xs text-ink-muted mt-0.5">Section {{ enr.section?.section_number }} · {{
                    enr.section?.course?.credits }} credits · {{ enr.section?.schedule_pattern || 'Schedule TBA' }}</p>
                </div>
              </div>
              <span class="px-3 py-1 rounded-full text-xs font-medium bg-success/12 text-[#047857]">{{
                enr.enrollment_status }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Available Sections -->
      <div class="bg-surface border border-border-light rounded-2xl shadow-card animate-fade-in delay-3">
        <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
          <div class="flex items-center gap-2">
            <div class="w-7 h-7 rounded-full bg-success/10 text-success flex items-center justify-center text-sm">
              <Icons name="mdi-playlist-plus" />
            </div>
            <h3 class="text-base font-semibold text-ink">Open Sections</h3>
          </div>
          <span class="px-3 py-1 rounded-full text-xs font-medium bg-sage/15 text-[#5e6e5f]">{{ availableSections.length
          }} available</span>
        </div>
        <div>
          <div v-if="loading" class="text-center py-8 text-ink-muted">
            <Icons name="mdi-loading" class="animate-spin w-6 h-6 mb-2" />
            <p>Loading...</p>
          </div>
          <div v-else-if="availableSections.length === 0" class="text-center py-10 text-ink-muted">
            <Icons name="mdi-information-outline" class="w-10 h-10 mb-2" />
            <p>No other sections available for registration at this time.</p>
          </div>
          <div v-else>
            <div v-for="section in availableSections" :key="section.section_id"
              class="flex flex-col sm:flex-row sm:items-center justify-between px-4 sm:px-6 py-4 border-b border-border-light last:border-b-0 hover:bg-primary/2.5 transition-colors gap-3">
              <div class="flex items-center gap-3">
                <div
                  class="w-10 h-10 rounded-full bg-sage/12 text-[#5e6e5f] flex items-center justify-center text-lg shrink-0">
                  <Icons name="mdi-book-outline" />
                </div>
                <div>
                  <p class="font-medium text-sm text-ink">{{ section.course?.course_code }} — {{
                    section.course?.course_name }}</p>
                  <p class="text-xs text-ink-muted mt-0.5">Section {{ section.section_number }} · {{
                    section.course?.credits }} credits · {{ section.schedule_pattern || 'Schedule TBA' }}</p>
                  <p class="text-xs text-success font-medium mt-0.5">{{ section.max_capacity - section.enrolled_count }}
                    seats available</p>
                </div>
              </div>
              <button @click="handleEnroll(section.section_id)"
                class="inline-flex items-center gap-2 px-5 py-2.5 bg-coral text-white border-none rounded-xl font-sans text-sm font-medium cursor-pointer transition-all duration-200 hover:bg-coral-hover hover:shadow-[0_4px_12px_rgba(224,122,95,0.3)]">
                <Icons name="mdi-plus" /> Enroll
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
