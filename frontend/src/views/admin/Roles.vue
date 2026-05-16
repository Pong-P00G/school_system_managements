<script setup>
import { onMounted, ref, computed } from 'vue'
import { getAdminRoles, createRole, updateRole, deleteRole } from '../../services/api'
import { getApiError, pick } from '../../components/utils/crud'
import { useToast } from '../../composables/useToast'
import ConfirmDeleteDialog from '../../components/ConfirmDeleteDialog.vue'

const toast = useToast()

const roles = ref([])
const totalRoles = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingRoleId = ref(null)

const showDeleteDialog = ref(false)
const deletingRoleId = ref(null)
const deleteRoleName = ref('')
const deleting = ref(false)

const defaultForm = () => ({ role_name: '', description: '', role_level: 99 })
const form = ref(defaultForm())

const levelColors = {
  0: 'bg-red-50 text-red-700 border border-red-200',
  1: 'bg-orange-50 text-orange-700 border border-orange-200',
  2: 'bg-amber-50 text-amber-700 border border-amber-200',
  3: 'bg-yellow-50 text-yellow-700 border border-yellow-200',
  4: 'bg-lime-50 text-lime-700 border border-lime-200',
  5: 'bg-green-50 text-green-700 border border-green-200',
  6: 'bg-teal-50 text-teal-700 border border-teal-200',
  7: 'bg-cyan-50 text-cyan-700 border border-cyan-200',
  8: 'bg-blue-50 text-blue-700 border border-blue-200',
}

const getLevelClass = (level) => levelColors[level] || 'bg-gray-50 text-gray-700 border border-gray-200'

const loadRoles = async () => {
  loading.value = true; error.value = ''
  try {
    const res = await getAdminRoles()
    roles.value = res.data.roles || res.data
    totalRoles.value = res.data.total || roles.value.length
  } catch (err) { error.value = getApiError(err, 'Failed to load roles') }
  finally { loading.value = false }
}

const openCreate = () => { editingRoleId.value = null; form.value = defaultForm(); error.value = ''; showModal.value = true }

const openEdit = (role) => {
  editingRoleId.value = role.role_id
  form.value = { role_name: role.role_name || '', description: role.description || '', role_level: role.role_level ?? 99 }
  error.value = ''
  showModal.value = true
}

const closeModal = () => { showModal.value = false; editingRoleId.value = null; form.value = defaultForm(); error.value = '' }

const saveRole = async () => {
  saving.value = true; error.value = ''
  try {
    const payload = pick(form.value, ['role_name', 'description', 'role_level'])
    payload.role_level = Number(payload.role_level)
    if (editingRoleId.value) {
      await updateRole(editingRoleId.value, payload)
      toast.success('Role updated successfully')
    } else {
      await createRole(payload)
      toast.success('Role created successfully')
    }
    closeModal()
    await loadRoles()
  } catch (err) { error.value = getApiError(err, 'Failed to save role') }
  finally { saving.value = false }
}

const confirmDeleteRole = (roleId, roleName) => {
  deletingRoleId.value = roleId
  deleteRoleName.value = roleName
  showDeleteDialog.value = true
}

const executeDeleteRole = async () => {
  deleting.value = true
  try {
    await deleteRole(deletingRoleId.value)
    showDeleteDialog.value = false
    await loadRoles()
    toast.success('Role deleted successfully')
  } catch (err) {
    toast.error(getApiError(err, 'Failed to delete role'))
    showDeleteDialog.value = false
  } finally {
    deleting.value = false
  }
}

onMounted(loadRoles)
</script>

<template>
  <div>
    <div class="admin-page-header">
      <div>
        <h1>Role Management</h1>
        <p class="text-sm text-ink-muted mt-1">Manage user roles and privilege levels. Lower level = higher privilege.</p>
      </div>
      <button class="admin-btn-add" @click="openCreate">
        <svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        Add Role
      </button>
    </div>

    <div v-if="error && !showModal" class="admin-error">{{ error }}</div>
    <div v-if="loading" class="admin-loading">Loading roles...</div>

    <div v-else class="admin-table-card">
      <div class="admin-record-count">{{ totalRoles }} role(s)</div>
      <table class="admin-table">
        <thead>
          <tr>
            <th class="w-20 text-center">Level</th>
            <th>Role Name</th>
            <th>Description</th>
            <th class="w-24 text-center">Type</th>
            <th class="w-32">Created</th>
            <th class="w-40 text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="role in roles" :key="role.role_id">
            <td class="text-center">
              <span class="inline-flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold" :class="getLevelClass(role.role_level)">
                {{ role.role_level }}
              </span>
            </td>
            <td class="cell-primary">
              <span class="font-medium">{{ role.role_name }}</span>
            </td>
            <td class="text-sm text-ink-secondary">{{ role.description || '—' }}</td>
            <td class="text-center">
              <span class="admin-badge" :class="role.is_system_role ? 'admin-badge-active' : 'admin-badge-inactive'">
                {{ role.is_system_role ? 'System' : 'Custom' }}
              </span>
            </td>
            <td class="text-sm text-ink-muted">{{ role.created_at ? new Date(role.created_at).toLocaleDateString() : '—' }}</td>
            <td class="text-center">
              <div class="inline-flex gap-1">
                <button class="admin-action-btn admin-action-edit" @click="openEdit(role)" title="Edit role">Edit</button>
                <button class="admin-action-btn admin-action-delete" @click="confirmDeleteRole(role.role_id, role.role_name)" title="Delete role">Delete</button>
              </div>
            </td>
          </tr>
          <tr v-if="roles.length === 0">
            <td colspan="6" class="text-center text-ink-muted py-8">
              <div class="flex flex-col items-center gap-2">
                <svg class="w-10 h-10 text-ink-muted opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                <span>No roles found. Click "Add Role" to create one.</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create / Edit Modal -->
    <div v-if="showModal" class="admin-modal-overlay" @click.self="closeModal">
      <div class="admin-modal admin-modal-sm">
        <div class="flex items-center justify-between mb-4">
          <h2 class="mb-0!">{{ editingRoleId ? 'Edit Role' : 'Create Role' }}</h2>
          <button @click="closeModal" class="text-ink-muted hover:text-ink transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
        <form class="admin-form-grid" @submit.prevent="saveRole">
          <div v-if="error" class="admin-error col-span-full mb-2!">{{ error }}</div>
          <div class="col-span-full">
            <label class="form-label">Role Name</label>
            <input v-model="form.role_name" placeholder="e.g. moderator" required maxlength="50" class="w-full" />
          </div>
          <div class="col-span-full">
            <label class="form-label">Role Level</label>
            <div class="flex items-center gap-3">
              <input v-model.number="form.role_level" type="number" min="0" max="99" required class="w-24" />
              <div class="flex-1">
                <div class="h-2 bg-gray-100 rounded-full overflow-hidden border border-gray-200">
                  <div class="h-full bg-primary rounded-full transition-all" :style="{width: Math.min(100, (form.role_level / 10) * 100) + '%'}"></div>
                </div>
                <div class="flex justify-between text-xs text-ink-muted mt-1">
                  <span>0 = Highest</span>
                  <span>99 = Lowest</span>
                </div>
              </div>
            </div>
          </div>
          <div class="col-span-full">
            <label class="form-label">Description</label>
            <textarea v-model="form.description" placeholder="Optional description of this role's purpose" rows="3" maxlength="500" class="w-full"></textarea>
          </div>
          <div class="admin-form-actions">
            <button type="button" class="admin-btn-cancel" @click="closeModal">Cancel</button>
            <button :disabled="saving" type="submit" class="admin-btn-save">
              {{ saving ? 'Saving...' : (editingRoleId ? 'Update Role' : 'Create Role') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete Confirmation -->
    <ConfirmDeleteDialog
      :show="showDeleteDialog"
      :item-name="deleteRoleName"
      :deleting="deleting"
      @confirm="executeDeleteRole"
      @cancel="showDeleteDialog = false"
    />
  </div>
</template>
