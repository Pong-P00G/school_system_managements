<script setup>
import { ref, onMounted } from 'vue'
import api, { getFacultySections } from '../../services/api'
import Icons from '../../components/icon/Icons.vue'
import { useToast } from '../../composables/useToast'

const toast = useToast()
const loading = ref(true)
const sections = ref([])
const announcements = ref([])
const showForm = ref(false)
const form = ref({ section_id: '', title: '', content: '', is_pinned: false })
const submitting = ref(false)

async function fetchData() {
  loading.value = true
  try {
    const secRes = await getFacultySections('me')
    sections.value = secRes.data.sections || []
    const annRes = await api.get('/announcements/my-sections')
    announcements.value = annRes.data || []
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function postAnnouncement() {
  if (!form.value.section_id || !form.value.title || !form.value.content) {
    toast.error('Please fill all fields'); return
  }
  submitting.value = true
  try {
    await api.post(`/announcements/?section_id=${form.value.section_id}&title=${encodeURIComponent(form.value.title)}&content=${encodeURIComponent(form.value.content)}&is_pinned=${form.value.is_pinned}`)
    toast.success('Announcement posted!')
    form.value = { section_id: '', title: '', content: '', is_pinned: false }
    showForm.value = false
    await fetchData()
  } catch (e) { toast.error(e.response?.data?.detail || 'Failed to post') }
  finally { submitting.value = false }
}

async function deleteAnnouncement(id) {
  if (!confirm('Delete this announcement?')) return
  try { await api.delete(`/announcements/${id}`); toast.success('Deleted'); await fetchData() }
  catch (e) { toast.error('Failed to delete') }
}

onMounted(fetchData)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
      <div>
        <h1 class="text-2xl font-bold text-ink tracking-tight">Announcements</h1>
        <p class="text-sm text-ink-muted mt-0.5">Post announcements to your class sections</p>
      </div>
      <button @click="showForm = !showForm"
        class="inline-flex items-center gap-2 px-5 py-2.5 bg-coral text-white border-none rounded-xl text-sm font-medium cursor-pointer transition-all hover:bg-coral-hover">
        <Icons :name="showForm ? 'mdi-close' : 'mdi-plus'" /> {{ showForm ? 'Cancel' : 'New Announcement' }}
      </button>
    </div>

    <!-- Post Form -->
    <div v-if="showForm" class="bg-surface border border-border-light rounded-xl shadow-card p-5 animate-fade-in">
      <form @submit.prevent="postAnnouncement" class="space-y-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Section *</label>
            <select v-model="form.section_id" required
              class="w-full px-3 py-2 text-sm border border-border-medium rounded-lg bg-page text-ink focus:outline-none focus:ring-2 focus:ring-primary/30">
              <option value="" disabled>Select section</option>
              <option v-for="s in sections" :key="s.section_id" :value="s.section_id">
                {{ s.course?.course_code }} — Sec {{ s.section_number }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Title *</label>
            <input v-model="form.title" required placeholder="Announcement title"
              class="w-full px-3 py-2 text-sm border border-border-medium rounded-lg bg-page text-ink focus:outline-none focus:ring-2 focus:ring-primary/30" />
          </div>
        </div>
        <div>
          <label class="block text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Content *</label>
          <textarea v-model="form.content" required rows="3" placeholder="Write your announcement..."
            class="w-full px-3 py-2 text-sm border border-border-medium rounded-lg bg-page text-ink focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"></textarea>
        </div>
        <div class="flex items-center justify-between">
          <label class="flex items-center gap-2 text-sm text-ink-secondary cursor-pointer">
            <input type="checkbox" v-model="form.is_pinned" class="w-4 h-4 accent-primary" /> Pin announcement
          </label>
          <button type="submit" :disabled="submitting"
            class="px-5 py-2 text-sm font-medium text-white bg-primary rounded-lg border-none cursor-pointer hover:bg-primary-dark transition disabled:opacity-50">
            {{ submitting ? 'Posting...' : 'Post' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-ink-muted">
      <Icons name="mdi-loading" class="animate-spin w-8 h-8 mb-2" /><p>Loading...</p>
    </div>

    <!-- Empty -->
    <div v-else-if="announcements.length === 0" class="bg-surface border border-border-light rounded-2xl shadow-card text-center py-12">
      <Icons name="mdi-bullhorn-outline" class="w-12 h-12 text-ink-muted mb-2" />
      <p class="text-ink-muted">No announcements yet. Post one to get started!</p>
    </div>

    <!-- List -->
    <div v-else class="space-y-3">
      <div v-for="ann in announcements" :key="ann.announcement_id"
        class="bg-surface border border-border-light rounded-xl shadow-card p-4 sm:p-5 animate-fade-in">
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-start gap-3 min-w-0">
            <div class="w-9 h-9 rounded-full flex items-center justify-center text-base shrink-0"
              :class="ann.is_pinned ? 'bg-coral/12 text-coral' : 'bg-primary/10 text-primary'">
              <Icons :name="ann.is_pinned ? 'mdi-pin' : 'mdi-bullhorn-outline'" />
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <h4 class="text-sm font-semibold text-ink">{{ ann.title }}</h4>
                <span class="px-2 py-0.5 rounded-full text-[0.65rem] font-medium bg-primary/10 text-primary">{{ ann.course_code }}</span>
              </div>
              <p class="text-sm text-ink-secondary mt-1 whitespace-pre-line">{{ ann.content }}</p>
              <p class="text-xs text-ink-muted mt-2">{{ ann.author_name }} · {{ new Date(ann.created_at).toLocaleDateString() }}</p>
            </div>
          </div>
          <button @click="deleteAnnouncement(ann.announcement_id)"
            class="p-1.5 rounded-lg text-ink-muted hover:text-error hover:bg-error/5 transition border-none bg-transparent cursor-pointer shrink-0">
            <Icons name="mdi-delete-outline" class="text-base" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
