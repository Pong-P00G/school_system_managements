<script setup>
import { onMounted, ref, computed } from 'vue'
import { getPagePermissions, updatePagePermission, getAdminRoles } from '../../services/api'
import { getApiError } from '../../components/utils/crud'
import { useToast } from '../../composables/useToast'

const toast = useToast()
const pages = ref([])
const roles = ref([])
const loading = ref(false)
const error = ref('')
const searchQuery = ref('')

const filteredPages = computed(() => {
  if (!searchQuery.value) return pages.value
  const q = searchQuery.value.toLowerCase()
  return pages.value.filter(p => p.page_name.toLowerCase().includes(q) || p.page_path.toLowerCase().includes(q))
})

const levelColors = {
  0: 'bg-red-100 text-red-800 border-red-200',
  1: 'bg-orange-100 text-orange-800 border-orange-200',
  2: 'bg-amber-100 text-amber-800 border-amber-200',
  3: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  4: 'bg-lime-100 text-lime-800 border-lime-200',
  5: 'bg-green-100 text-green-800 border-green-200',
  6: 'bg-teal-100 text-teal-800 border-teal-200',
  7: 'bg-cyan-100 text-cyan-800 border-cyan-200',
  8: 'bg-blue-100 text-blue-800 border-blue-200',
}

const getLevelClass = (level) => levelColors[level] || 'bg-gray-100 text-gray-800 border-gray-200'

const loadData = async () => {
  loading.value = true; error.value = ''
  try {
    const [pagesRes, rolesRes] = await Promise.all([getPagePermissions(), getAdminRoles()])
    pages.value = pagesRes.data
    const rolesData = rolesRes.data.roles || rolesRes.data
    roles.value = rolesData.sort((a, b) => a.role_level - b.role_level)
  } catch (err) { error.value = getApiError(err, 'Failed to load') }
  finally { loading.value = false }
}

const updateLevel = async (page, newLevel) => {
  try {
    await updatePagePermission(page.id, { min_role_level: Number(newLevel) })
    page.min_role_level = Number(newLevel)
    toast.success(`"${page.page_name}" access updated to level ${newLevel}`)
  } catch (err) { toast.error(getApiError(err, 'Failed to update')) }
}

const getAccessibleRoles = (level) => roles.value.filter(r => r.role_level <= level)

onMounted(loadData)
</script>

<template>
  <div>
    <div class="admin-page-header">
      <div>
        <h1>Page Permissions</h1>
        <p class="text-sm text-ink-muted mt-1">Control which roles can access each page. Lower level number = higher privilege.</p>
      </div>
    </div>

    <div v-if="error" class="admin-error">{{ error }}</div>
    <div v-if="loading" class="admin-loading">Loading...</div>

    <template v-else>
      <!-- Role Level Legend -->
      <div class="bg-surface rounded-xl border border-border-light p-4 mb-4 shadow-card">
        <h3 class="text-sm font-semibold text-ink mb-3">Role Hierarchy</h3>
        <div class="flex flex-wrap gap-2">
          <span v-for="role in roles" :key="role.role_id"
            class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border"
            :class="getLevelClass(role.role_level)">
            <span class="font-bold">{{ role.role_level }}</span>
            <span>{{ role.role_name }}</span>
          </span>
        </div>
      </div>

      <!-- Search -->
      <div class="mb-4">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search pages..."
          class="w-full max-w-sm px-3 py-2 border border-border-light rounded-lg text-sm focus:outline-none focus:border-primary"
        />
      </div>

      <!-- Pages Table -->
      <div class="admin-table-card">
        <div class="admin-record-count">{{ filteredPages.length }} page(s)</div>
        <table class="admin-table">
          <thead>
            <tr>
              <th>Page</th>
              <th class="w-48">Path</th>
              <th class="w-56">Min Level Required</th>
              <th>Accessible By</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="page in filteredPages" :key="page.id">
              <td class="cell-primary">
                <div class="flex items-center gap-2">
                  <svg class="w-4 h-4 text-ink-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                  <span class="font-medium">{{ page.page_name }}</span>
                </div>
              </td>
              <td>
                <code class="text-xs bg-gray-50 px-2 py-0.5 rounded text-ink-secondary">{{ page.page_path }}</code>
              </td>
              <td>
                <select
                  :value="page.min_role_level"
                  @change="updateLevel(page, $event.target.value)"
                  class="w-full border border-border-light rounded-lg px-3 py-1.5 text-sm bg-surface focus:outline-none focus:border-primary cursor-pointer"
                >
                  <option v-for="role in roles" :key="role.role_id" :value="role.role_level">
                    Level {{ role.role_level }} — {{ role.role_name }}
                  </option>
                  <option :value="99">Level 99 — No access</option>
                </select>
              </td>
              <td>
                <div class="flex flex-wrap gap-1">
                  <span v-for="role in getAccessibleRoles(page.min_role_level)" :key="role.role_id"
                    class="inline-block px-2 py-0.5 rounded text-xs font-medium border"
                    :class="getLevelClass(role.role_level)">
                    {{ role.role_name }}
                  </span>
                  <span v-if="getAccessibleRoles(page.min_role_level).length === 0" class="text-xs text-ink-muted italic">
                    No roles
                  </span>
                </div>
              </td>
            </tr>
            <tr v-if="filteredPages.length === 0">
              <td colspan="4" class="text-center text-ink-muted py-8">
                <span v-if="searchQuery">No pages match "{{ searchQuery }}"</span>
                <span v-else>No page permissions configured.</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
