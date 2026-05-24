<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../services/api'
import Icons from '../../components/icon/Icons.vue'
import { useToast } from '../../composables/useToast'

const route = useRoute()
const router = useRouter()
const toast = useToast()

const loading = ref(true)
const enrollment = ref(null)
const withdrawalRequests = ref([])
const showWithdrawForm = ref(false)
const reason = ref('')
const submitting = ref(false)

const enrollmentId = computed(() => route.params.enrollmentId)
const course = computed(() => enrollment.value?.section?.course)
const section = computed(() => enrollment.value?.section)
const hasPendingRequest = computed(() => withdrawalRequests.value.some(r => r.status === 'pending'))
const announcements = ref([])

async function fetchData() {
  loading.value = true
  try {
    const enrRes = await api.get(`/enrollments/${enrollmentId.value}`)
    enrollment.value = enrRes.data
    // Fetch withdrawal requests separately (table may not exist yet)
    try {
      const reqRes = await api.get(`/enrollments/${enrollmentId.value}/withdrawal-request`)
      withdrawalRequests.value = reqRes.data
    } catch (_) {}
    // Fetch announcements for this section
    try {
      if (enrollment.value?.section_id) {
        const annRes = await api.get(`/announcements/section/${enrollment.value.section_id}`)
        announcements.value = annRes.data || []
      }
    } catch (_) {}
  } catch (e) {
    toast.error('Failed to load course details')
    router.push('/student/courses')
  } finally {
    loading.value = false
  }
}

async function submitWithdrawal() {
  if (!reason.value.trim() || reason.value.trim().length < 5) {
    toast.error('Please provide a reason (at least 5 characters)')
    return
  }
  submitting.value = true
  try {
    await api.post(`/enrollments/${enrollmentId.value}/withdrawal-request?reason=${encodeURIComponent(reason.value.trim())}`)
    toast.success('Withdrawal request submitted successfully')
    reason.value = ''
    showWithdrawForm.value = false
    await fetchData()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to submit request')
  } finally {
    submitting.value = false
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <!-- Back -->
    <button @click="router.push('/student/courses')"
      class="flex items-center gap-1.5 text-sm text-ink-muted font-medium mb-4 bg-transparent border-none cursor-pointer hover:text-primary transition p-0">
      <Icons name="mdi-arrow-left" class="text-base" /> Back to Courses
    </button>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-16">
      <Icons name="mdi-loading" class="text-3xl animate-spin text-primary" />
    </div>

    <template v-else-if="enrollment">
      <!-- Course Header -->
      <div class="bg-primary rounded-2xl p-5 sm:p-7 text-white relative overflow-hidden mb-6">
        <div class="absolute -top-[40%] -right-[10%] w-64 h-64 bg-white/6 rounded-full"></div>
        <div class="relative z-10">
          <p class="text-xs uppercase tracking-widest opacity-70 mb-1">{{ course?.course_code }}</p>
          <h1 class="text-xl sm:text-2xl font-bold mb-3">{{ course?.course_name }}</h1>
          <div class="flex flex-wrap gap-2">
            <span class="px-3 py-1 rounded-full text-xs font-medium bg-white/15">Section {{ section?.section_number }}</span>
            <span class="px-3 py-1 rounded-full text-xs font-medium bg-white/15">{{ course?.credits }} Credits</span>
            <span class="px-3 py-1 rounded-full text-xs font-medium bg-white/15 capitalize">{{ enrollment.enrollment_status }}</span>
          </div>
        </div>
      </div>

      <!-- Course Details Card -->
      <div class="bg-surface border border-border-light rounded-xl shadow-card p-4 sm:p-6 mb-6">
        <h3 class="text-sm font-semibold text-ink mb-4">Course Information</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <span class="text-xs text-ink-muted uppercase tracking-wide">Schedule</span>
            <p class="mt-0.5 text-ink">{{ section?.schedule_pattern || 'TBA' }}</p>
          </div>
          <div>
            <span class="text-xs text-ink-muted uppercase tracking-wide">Room</span>
            <p class="mt-0.5 text-ink">{{ section?.room?.room_number || 'TBA' }}</p>
          </div>
          <div>
            <span class="text-xs text-ink-muted uppercase tracking-wide">Term</span>
            <p class="mt-0.5 text-ink">{{ section?.term?.term_name || 'N/A' }}</p>
          </div>
          <div>
            <span class="text-xs text-ink-muted uppercase tracking-wide">Enrolled On</span>
            <p class="mt-0.5 text-ink">{{ new Date(enrollment.enrollment_date).toLocaleDateString() }}</p>
          </div>
          <div v-if="course?.description" class="sm:col-span-2">
            <span class="text-xs text-ink-muted uppercase tracking-wide">Description</span>
            <p class="mt-0.5 text-ink">{{ course.description }}</p>
          </div>
        </div>
      </div>

      <!-- Announcements -->
      <div v-if="announcements.length > 0" class="bg-surface border border-border-light rounded-xl shadow-card p-4 sm:p-6 mb-6">
        <h3 class="text-sm font-semibold text-ink mb-3 flex items-center gap-2">
          <Icons name="mdi-bullhorn-outline" class="text-base text-coral" /> Announcements
        </h3>
        <div class="space-y-3">
          <div v-for="ann in announcements" :key="ann.announcement_id"
            class="p-3 rounded-lg border border-border-light" :class="ann.is_pinned ? 'bg-coral/5 border-coral/20' : 'bg-page'">
            <div class="flex items-center gap-2 mb-1">
              <Icons v-if="ann.is_pinned" name="mdi-pin" class="text-xs text-coral" />
              <span class="text-sm font-medium text-ink">{{ ann.title }}</span>
            </div>
            <p class="text-xs text-ink-secondary whitespace-pre-line">{{ ann.content }}</p>
            <p class="text-xs text-ink-muted mt-1.5">{{ ann.author_name }} · {{ new Date(ann.created_at).toLocaleDateString() }}</p>
          </div>
        </div>
      </div>

      <!-- Withdrawal Section -->
      <div v-if="enrollment.enrollment_status === 'enrolled'" class="bg-surface border border-border-light rounded-xl shadow-card p-4 sm:p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-semibold text-ink">Course Withdrawal</h3>
          <button v-if="!showWithdrawForm && !hasPendingRequest" @click="showWithdrawForm = true"
            class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-error border border-error/30 rounded-lg bg-transparent cursor-pointer hover:bg-error/5 transition">
            <Icons name="mdi-exit-run" class="text-sm" /> Request to Leave
          </button>
        </div>

        <!-- Pending Request Notice -->
        <div v-if="hasPendingRequest" class="flex items-start gap-3 p-3 rounded-lg bg-warning/10 border border-warning/20">
          <Icons name="mdi-clock-outline" class="text-lg text-warning shrink-0 mt-0.5" />
          <div>
            <p class="text-sm font-medium text-ink">Withdrawal request pending</p>
            <p class="text-xs text-ink-muted mt-0.5">Your request is being reviewed by the administration.</p>
          </div>
        </div>

        <!-- Withdrawal Form -->
        <form v-if="showWithdrawForm" @submit.prevent="submitWithdrawal" class="space-y-4">
          <div class="p-3 rounded-lg bg-error/5 border border-error/15">
            <p class="text-xs text-error font-medium mb-1">⚠️ Important</p>
            <p class="text-xs text-ink-muted">This will send a withdrawal request to the administration. You will remain enrolled until the request is approved.</p>
          </div>
          <div>
            <label class="block text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Reason for leaving *</label>
            <textarea v-model="reason" rows="3" required minlength="5" placeholder="Please explain why you want to withdraw from this course..."
              class="w-full px-3 py-2 text-sm border border-border-medium rounded-lg bg-page text-ink focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary resize-none"></textarea>
          </div>
          <div class="flex flex-col-reverse sm:flex-row gap-2">
            <button type="submit" :disabled="submitting"
              class="px-4 py-2.5 text-xs font-medium text-white bg-error rounded-lg cursor-pointer hover:bg-red-600 transition disabled:opacity-50 w-full sm:w-auto">
              {{ submitting ? 'Submitting...' : 'Submit Request' }}
            </button>
            <button type="button" @click="showWithdrawForm = false"
              class="px-4 py-2.5 text-xs font-medium text-ink-secondary border border-border-medium rounded-lg bg-transparent cursor-pointer hover:bg-page transition w-full sm:w-auto">
              Cancel
            </button>
          </div>
        </form>

        <!-- No form, no pending -->
        <p v-if="!showWithdrawForm && !hasPendingRequest" class="text-xs text-ink-muted">
          If you need to leave this course, you can submit a withdrawal request with a reason.
        </p>
      </div>

      <!-- Withdrawn status -->
      <div v-else-if="enrollment.enrollment_status === 'withdrawn'" class="bg-surface border border-border-light rounded-xl shadow-card p-4 sm:p-6">
        <div class="flex items-start gap-3 p-3 rounded-lg bg-ink-muted/5">
          <Icons name="mdi-information-outline" class="text-lg text-ink-muted shrink-0 mt-0.5" />
          <div>
            <p class="text-sm font-medium text-ink">Withdrawn from this course</p>
            <p v-if="enrollment.withdrawal_reason" class="text-xs text-ink-muted mt-0.5">Reason: {{ enrollment.withdrawal_reason }}</p>
          </div>
        </div>
      </div>

      <!-- Previous Requests -->
      <div v-if="withdrawalRequests.length > 0" class="bg-surface border border-border-light rounded-xl shadow-card p-4 sm:p-6 mt-6">
        <h3 class="text-sm font-semibold text-ink mb-3">Request History</h3>
        <div class="space-y-3">
          <div v-for="req in withdrawalRequests" :key="req.request_id"
            class="flex items-start gap-3 p-3 rounded-lg border border-border-light">
            <Icons :name="req.status === 'approved' ? 'mdi-check-circle' : req.status === 'rejected' ? 'mdi-close-circle' : 'mdi-clock-outline'"
              :class="req.status === 'approved' ? 'text-success' : req.status === 'rejected' ? 'text-error' : 'text-warning'"
              class="text-lg shrink-0 mt-0.5" />
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-xs font-semibold capitalize" :class="req.status === 'approved' ? 'text-success' : req.status === 'rejected' ? 'text-error' : 'text-warning'">{{ req.status }}</span>
                <span class="text-xs text-ink-muted">{{ new Date(req.created_at).toLocaleDateString() }}</span>
              </div>
              <p class="text-xs text-ink mt-1">{{ req.reason }}</p>
              <p v-if="req.reviewer_note" class="text-xs text-ink-muted mt-1 italic">Note: {{ req.reviewer_note }}</p>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
