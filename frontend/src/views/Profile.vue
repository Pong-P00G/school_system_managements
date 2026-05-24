<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import api, { getMyStudentProfile, getFacultyProfile } from '../services/api'
import Icons from '../components/icon/Icons.vue'

const authStore = useAuthStore()
const loading = ref(true)
const editing = ref(false)
const saving = ref(false)
const message = ref('')
const messageType = ref('')
const profile = ref(null)

const isStudent = computed(() => authStore.isStudent)
const isTeacher = computed(() => authStore.isTeacher)

const user = computed(() => authStore.user || {})
const userInitial = computed(() => (user.value.username || 'U').charAt(0).toUpperCase())

const form = ref({
  email: '',
  phone_number: '',
  address: ''
})

async function fetchProfile() {
  loading.value = true
  try {
    if (isStudent.value) {
      const res = await getMyStudentProfile()
      profile.value = res.data
    } else if (isTeacher.value) {
      try {
        const res = await getFacultyProfile()
        profile.value = res.data
      } catch (e) {
        // Faculty profile may not exist yet, fall back to user info
        const res = await api.get('/users/me')
        profile.value = res.data
      }
    } else {
      const res = await api.get('/users/me')
      profile.value = res.data
    }
    form.value.email = profile.value?.email || user.value.email || ''
    form.value.phone_number = profile.value?.phone_number || ''
    form.value.address = profile.value?.address || ''
  } catch (e) {
    console.error('Failed to load profile:', e)
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  saving.value = true
  message.value = ''
  try {
    if (isStudent.value && profile.value?.student_id) {
      await api.put(`/students/${profile.value.student_id}`, form.value)
    } else if (isTeacher.value && profile.value?.faculty_id) {
      await api.put(`/faculty/${profile.value.faculty_id}`, form.value)
    } else {
      await api.put(`/users/${user.value.user_id}`, form.value)
    }
    message.value = 'Profile updated successfully!'
    messageType.value = 'success'
    editing.value = false
    await fetchProfile()
  } catch (e) {
    message.value = e.response?.data?.detail || 'Failed to update profile'
    messageType.value = 'error'
  } finally {
    saving.value = false
  }
}

function cancelEdit() {
  editing.value = false
  form.value.email = profile.value?.email || user.value.email || ''
  form.value.phone_number = profile.value?.phone_number || ''
  form.value.address = profile.value?.address || ''
}

onMounted(fetchProfile)
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <h1 class="text-2xl font-bold text-ink mb-6">My Profile</h1>

    <!-- Message -->
    <div v-if="message" class="mb-4 px-4 py-3 rounded-lg text-sm font-medium"
      :class="messageType === 'success' ? 'bg-success/10 text-success' : 'bg-error/10 text-error'">
      {{ message }}
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-16">
      <Icons name="mdi-loading" class="text-3xl animate-spin text-primary" />
    </div>

    <!-- Profile Card -->
    <div v-else class="bg-surface rounded-xl shadow-card p-4 sm:p-6 space-y-5 sm:space-y-6">
      <!-- Avatar & Name -->
      <div class="flex items-center gap-3 sm:gap-4 pb-5 border-b border-border-light">
        <div class="w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-primary text-white text-xl sm:text-2xl font-bold flex items-center justify-center shrink-0">
          {{ userInitial }}
        </div>
        <div class="min-w-0">
          <h2 class="text-base sm:text-lg font-semibold text-ink truncate">{{ user.username }}</h2>
          <span class="text-sm text-ink-muted capitalize">{{ authStore.userRole }}</span>
        </div>
      </div>

      <!-- Info Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="text-xs font-medium text-ink-muted uppercase tracking-wide">Username</label>
          <p class="mt-1 text-sm text-ink">{{ user.username }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-ink-muted uppercase tracking-wide">Role</label>
          <p class="mt-1 text-sm text-ink capitalize">{{ authStore.userRole }}</p>
        </div>

        <!-- Student-specific fields -->
        <template v-if="isStudent && profile">
          <div>
            <label class="text-xs font-medium text-ink-muted uppercase tracking-wide">Student ID</label>
            <p class="mt-1 text-sm text-ink">{{ profile.student_code || profile.student_id }}</p>
          </div>
          <div>
            <label class="text-xs font-medium text-ink-muted uppercase tracking-wide">Program</label>
            <p class="mt-1 text-sm text-ink">{{ profile.program?.program_name || 'N/A' }}</p>
          </div>
          <div>
            <label class="text-xs font-medium text-ink-muted uppercase tracking-wide">Enrollment Status</label>
            <p class="mt-1 text-sm text-ink capitalize">{{ profile.enrollment_status || 'N/A' }}</p>
          </div>
          <div>
            <label class="text-xs font-medium text-ink-muted uppercase tracking-wide">Academic Standing</label>
            <p class="mt-1 text-sm text-ink capitalize">{{ profile.academic_standing || 'N/A' }}</p>
          </div>
        </template>

        <!-- Teacher-specific fields -->
        <template v-if="isTeacher && profile">
          <div>
            <label class="text-xs font-medium text-ink-muted uppercase tracking-wide">Faculty ID</label>
            <p class="mt-1 text-sm text-ink">{{ profile.faculty_code || profile.faculty_id }}</p>
          </div>
          <div>
            <label class="text-xs font-medium text-ink-muted uppercase tracking-wide">Department</label>
            <p class="mt-1 text-sm text-ink">{{ profile.department?.department_name || 'N/A' }}</p>
          </div>
          <div>
            <label class="text-xs font-medium text-ink-muted uppercase tracking-wide">Rank</label>
            <p class="mt-1 text-sm text-ink capitalize">{{ profile.faculty_rank || 'N/A' }}</p>
          </div>
          <div>
            <label class="text-xs font-medium text-ink-muted uppercase tracking-wide">Employment Status</label>
            <p class="mt-1 text-sm text-ink capitalize">{{ profile.employment_status || 'N/A' }}</p>
          </div>
        </template>
      </div>

      <!-- Editable Fields -->
      <div class="pt-5 border-t border-border-light">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-semibold text-ink">Contact Information</h3>
          <button v-if="!editing" @click="editing = true"
            class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-primary border border-primary/30 rounded-lg bg-transparent cursor-pointer hover:bg-primary/5 transition">
            <Icons name="mdi-pencil" class="text-sm" /> Edit
          </button>
        </div>

        <div v-if="!editing" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="text-xs font-medium text-ink-muted uppercase tracking-wide">Email</label>
            <p class="mt-1 text-sm text-ink">{{ form.email || 'Not set' }}</p>
          </div>
          <div>
            <label class="text-xs font-medium text-ink-muted uppercase tracking-wide">Phone</label>
            <p class="mt-1 text-sm text-ink">{{ form.phone_number || 'Not set' }}</p>
          </div>
          <div class="sm:col-span-2">
            <label class="text-xs font-medium text-ink-muted uppercase tracking-wide">Address</label>
            <p class="mt-1 text-sm text-ink">{{ form.address || 'Not set' }}</p>
          </div>
        </div>

        <form v-else @submit.prevent="saveProfile" class="space-y-4">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Email</label>
              <input v-model="form.email" type="email"
                class="w-full px-3 py-2 text-sm border border-border-medium rounded-lg bg-page text-ink focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div>
              <label class="block text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Phone</label>
              <input v-model="form.phone_number" type="tel"
                class="w-full px-3 py-2 text-sm border border-border-medium rounded-lg bg-page text-ink focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div class="sm:col-span-2">
              <label class="block text-xs font-medium text-ink-muted uppercase tracking-wide mb-1">Address</label>
              <input v-model="form.address" type="text"
                class="w-full px-3 py-2 text-sm border border-border-medium rounded-lg bg-page text-ink focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
          </div>
          <div class="flex flex-col-reverse sm:flex-row gap-2 pt-2">
            <button type="submit" :disabled="saving"
              class="px-4 py-2.5 text-xs font-medium text-white bg-primary rounded-lg cursor-pointer hover:bg-primary-dark transition disabled:opacity-50 w-full sm:w-auto">
              {{ saving ? 'Saving...' : 'Save Changes' }}
            </button>
            <button type="button" @click="cancelEdit"
              class="px-4 py-2.5 text-xs font-medium text-ink-secondary border border-border-medium rounded-lg bg-transparent cursor-pointer hover:bg-page transition w-full sm:w-auto">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
