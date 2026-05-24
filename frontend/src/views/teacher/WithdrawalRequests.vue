<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../../services/api'
import Icons from '../../components/icon/Icons.vue'
import { useToast } from '../../composables/useToast'

const toast = useToast()
const loading = ref(true)
const requests = ref([])
const filter = ref('pending')

const filteredRequests = computed(() => {
  if (filter.value === 'all') return requests.value
  return requests.value.filter(r => r.status === filter.value)
})

async function fetchRequests() {
  loading.value = true
  try {
    const res = await api.get('/enrollments/withdrawal-requests/all')
    requests.value = res.data.requests || []
  } catch (e) {
    console.error('Failed to load requests:', e)
  } finally {
    loading.value = false
  }
}

async function handleReview(requestId, action) {
  const note = action === 'rejected' ? prompt('Reason for rejection (optional):') : null
  try {
    await api.put(`/enrollments/withdrawal-requests/${requestId}/review?action=${action}${note ? '&note=' + encodeURIComponent(note) : ''}`)
    toast.success(`Request ${action}`)
    await fetchRequests()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to process request')
  }
}

onMounted(fetchRequests)
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-ink tracking-tight">Withdrawal Requests</h1>
      <p class="text-sm text-ink-muted mt-0.5">Review and manage student course withdrawal requests</p>
    </div>

    <!-- Filter -->
    <div class="flex gap-2">
      <button v-for="f in ['pending', 'approved', 'rejected', 'all']" :key="f" @click="filter = f"
        class="px-4 py-2 rounded-lg text-xs font-medium border cursor-pointer transition capitalize"
        :class="filter === f ? 'bg-primary text-white border-primary' : 'bg-surface text-ink-secondary border-border-light hover:bg-page'">
        {{ f }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-ink-muted">
      <Icons name="mdi-loading" class="animate-spin w-8 h-8 mb-2" />
      <p>Loading requests...</p>
    </div>

    <!-- Empty -->
    <div v-else-if="filteredRequests.length === 0" class="bg-surface border border-border-light rounded-2xl shadow-card text-center py-12">
      <Icons name="mdi-clipboard-check-outline" class="w-12 h-12 text-ink-muted mb-2" />
      <p class="text-ink-muted">No {{ filter !== 'all' ? filter : '' }} withdrawal requests</p>
    </div>

    <!-- Requests List -->
    <div v-else class="space-y-3">
      <div v-for="req in filteredRequests" :key="req.request_id"
        class="bg-surface border border-border-light rounded-xl shadow-card p-4 sm:p-5 animate-fade-in">
        <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
          <div class="flex items-start gap-3">
            <div class="w-10 h-10 rounded-full bg-warning/10 text-warning flex items-center justify-center text-lg shrink-0">
              <Icons name="mdi-account-arrow-right" />
            </div>
            <div>
              <p class="font-medium text-sm text-ink">{{ req.student_name }}</p>
              <p class="text-xs text-ink-muted mt-0.5">{{ req.course_code }} — {{ req.course_name }}</p>
              <div class="mt-2 p-2.5 bg-page rounded-lg border border-border-light">
                <p class="text-xs text-ink-secondary italic">"{{ req.reason }}"</p>
              </div>
              <p class="text-xs text-ink-muted mt-2">Submitted {{ new Date(req.created_at).toLocaleDateString() }}</p>
              <p v-if="req.reviewer_note" class="text-xs text-ink-muted mt-1">Note: {{ req.reviewer_note }}</p>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <span v-if="req.status !== 'pending'" class="px-3 py-1 rounded-full text-xs font-medium capitalize"
              :class="req.status === 'approved' ? 'bg-success/12 text-success' : 'bg-error/12 text-error'">
              {{ req.status }}
            </span>
            <template v-if="req.status === 'pending'">
              <button @click="handleReview(req.request_id, 'approved')"
                class="px-3 py-1.5 text-xs font-medium text-white bg-success rounded-lg border-none cursor-pointer hover:bg-emerald-600 transition">
                Approve
              </button>
              <button @click="handleReview(req.request_id, 'rejected')"
                class="px-3 py-1.5 text-xs font-medium text-white bg-error rounded-lg border-none cursor-pointer hover:bg-red-600 transition">
                Reject
              </button>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
