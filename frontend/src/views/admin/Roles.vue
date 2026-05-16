<script setup>
import { onMounted, ref } from 'vue'
import { getRoles, createRole, updateRole, deleteRole } from '../../services/api'
import { getApiError, pick } from '../../components/utils/crud'
import { useToast } from '../../composables/useToast'
import ConfirmDeleteDialog from '../../components/ConfirmDeleteDialog.vue'

const toast = useToast()

const roles = ref([])
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingRoleId = ref(null)

const showDeleteDialog = ref(false)
const deletingRoleId = ref(null)
const deleteRoleName = ref('')
const deleteDependencies = ref([])
const deleting = ref(false)

const defaultForm = () => ({ role_name: '', description: '', role_level: 99 })
const form = ref(defaultForm())

const loadRoles = async () => {
  loading.value = true; error.value = ''
  try {
    const res = await getRoles()
    roles.value = res.data
  } catch (err) { error.value = getApiError(err, 'Failed to load roles') }
  finally { loading.value = false }
}

const openCreate = () => { editingRoleId.value = null; form.value = defaultForm(); showModal.value = true }

const openEdit = (role) => {
  editingRoleId.value = role.role_id
  form.value = { role_name: role.role_name || '', description: role.description || '', role_level: role.role_level ?? 99 }
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
  deleteDependencies.value = []
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
      <h1>Role Management</h1>
      <button class="admin-btn-add" @click="openCreate">+ Add Role</button>
    </div>

    <div v-if="error && !showModal" class="admin-error">{{ error }}</div>
    <div v-if="loading" class="admin-loading">Loading roles...</div>

    <div v-else class="admin-table-card">
      <div class="admin-record-count">{{ roles.length }} role(s)</div>
      <table class="admin-table">
        <thead>
          <tr>
            <th>Level</th>
            <th>Role Name</th>
            <th>Description</th>
            <th>Type</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="role in roles" :key="role.role_id">
            <td class="text-center font-mono font-bold">{{ role.role_level }}</td>
            <td class="cell-primary">{{ role.role_name }}</td>
            <td>{{ role.description || '—' }}</td>
            <td>
              <span class="admin-badge" :class="role.is_system_role ? 'admin-badge-active' : 'admin-badge-inactive'">
                {{ role.is_system_role ? 'System' : 'Custom' }}
              </span>
            </td>
            <td class="text-sm text-ink-muted">{{ role.created_at ? new Date(role.created_at).toLocaleDateString() : '—' }}</td>
            <td>
              <button class="admin-action-btn admin-action-edit" @click="openEdit(role)">Edit</button>
              <button class="admin-action-btn admin-action-delete" @click="confirmDeleteRole(role.role_id, role.role_name)">Delete</button>
            </td>
          </tr>
          <tr v-if="roles.length === 0">
            <td colspan="6" class="text-center text-ink-muted py-6">No roles found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create / Edit Modal -->
    <div v-if="showModal" class="admin-modal-overlay">
      <div class="admin-modal admin-modal-sm">
        <h2>{{ editingRoleId ? 'Edit Role' : 'Create Role' }}</h2>
        <form class="admin-form-grid" @submit.prevent="saveRole">
          <div v-if="error" class="admin-error col-span-full">{{ error }}</div>
          <div class="col-span-full">
            <label class="form-label">Role Name</label>
            <input v-model="form.role_name" placeholder="e.g. moderator" required maxlength="50" />
          </div>
          <div class="col-span-full">
            <label class="form-label">Role Level</label>
            <input v-model.number="form.role_level" type="number" min="0" max="99" required />
            <p class="text-xs text-ink-muted mt-1">Lower number = higher privilege (0 = super-admin)</p>
          </div>
          <div class="col-span-full">
            <label class="form-label">Description</label>
            <textarea v-model="form.description" placeholder="Optional description" rows="3" maxlength="500"></textarea>
          </div>
          <div class="admin-form-actions">
            <button type="button" class="admin-btn-cancel" @click="closeModal">Cancel</button>
            <button :disabled="saving" type="submit" class="admin-btn-save">
              {{ saving ? 'Saving...' : (editingRoleId ? 'Update' : 'Create') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete Confirmation -->
    <ConfirmDeleteDialog
      :visible="showDeleteDialog"
      :item-name="deleteRoleName"
      :dependencies="deleteDependencies"
      :deleting="deleting"
      @confirm="executeDeleteRole"
      @force-delete="executeDeleteRole"
      @cancel="showDeleteDialog = false"
    />
  </div>
</template>
