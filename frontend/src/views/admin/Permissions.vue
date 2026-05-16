<script setup>
import { onMounted, ref } from 'vue'
import { getPagePermissions, updatePagePermission, getRoles } from '../../services/api'
import { getApiError } from '../../components/utils/crud'
import { useToast } from '../../composables/useToast'

const toast = useToast()
const pages = ref([])
const roles = ref([])
const loading = ref(false)
const error = ref('')

const loadData = async () => {
  loading.value = true; error.value = ''
  try {
    const [pagesRes, rolesRes] = await Promise.all([getPagePermissions(), getRoles()])
    pages.value = pagesRes.data
    roles.value = rolesRes.data.sort((a, b) => a.role_level - b.role_level)
  } catch (err) { error.value = getApiError(err, 'Failed to load') }
  finally { loading.value = false }
}

const updateLevel = async (page, newLevel) => {
  try {
    await updatePagePermission(page.id, { min_role_level: Number(newLevel) })
    page.min_role_level = Number(newLevel)
    toast.success(`Updated "${page.page_name}" to level ${newLevel}`)
  } catch (err) { toast.error(getApiError(err, 'Failed to update')) }
}

const getLevelLabel = (level) => {
  const role = roles.value.find(r => r.role_level === level)
  return role ? `${level} (${role.role_name})` : `${level}`
}

onMounted(loadData)
</script>

<template>
  <div>
    <div class="admin-page-header">
      <h1>Page Permissions</h1>
      <p class="text-sm text-ink-muted">Set minimum role level required to access each page. Lower level = higher privilege.</p>
    </div>

    <div v-if="error" class="admin-error">{{ error }}</div>
    <div v-if="loading" class="admin-loading">Loading...</div>

    <div v-else class="admin-table-card">
      <!-- Role level reference -->
      <div class="mb-4 p-3 bg-surface-alt rounded-lg">
        <span class="text-sm font-medium">Role Levels: </span>
        <span v-for="role in roles" :key="role.role_id" class="inline-block mr-3 text-xs">
          <span class="font-mono font-bold">{{ role.role_level }}</span> = {{ role.role_name }}
        </span>
      </div>

      <table class="admin-table">
        <thead>
          <tr>
            <th>Page</th>
            <th>Path</th>
            <th>Min Level Required</th>
            <th>Accessible By</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="page in pages" :key="page.id">
            <td class="cell-primary">{{ page.page_name }}</td>
            <td class="text-sm font-mono text-ink-muted">{{ page.page_path }}</td>
            <td>
              <select
                :value="page.min_role_level"
                @change="updateLevel(page, $event.target.value)"
                class="border rounded px-2 py-1 text-sm"
              >
                <option v-for="role in roles" :key="role.role_id" :value="role.role_level">
                  {{ role.role_level }} - {{ role.role_name }}
                </option>
                <option :value="99">99 - No access</option>
              </select>
            </td>
            <td class="text-sm text-ink-muted">
              <span v-for="role in roles.filter(r => r.role_level <= page.min_role_level)" :key="role.role_id" class="inline-block mr-1">
                <span class="admin-badge admin-badge-active text-xs">{{ role.role_name }}</span>
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
