<script setup>
import { onMounted, ref } from 'vue'
import { createUser, deleteUser, getUsers, updateUser, getRoles, assignRole, removeRole } from '../services/api'
import { getApiError, pick } from '../components/utils/crud'
import { useToast } from '../composables/useToast'
import Pagination from '../components/Pagination.vue'
import SearchFilter from '../components/SearchFilter.vue'
import ConfirmDeleteDialog from '../components/ConfirmDeleteDialog.vue'

const toast = useToast()

const users = ref([])
const roles = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingUserId = ref(null)
const currentPage = ref(1)
const pageSize = 100
const searchQuery = ref('')

const selectedIds = ref(new Set())
const selectAll = () => {
  if (selectedIds.value.size === users.value.length) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(users.value.map(u => u.user_id))
  }
}
const toggleSelect = (id) => {
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id); else next.add(id)
  selectedIds.value = next
}

const showDeleteDialog = ref(false)
const deletingUserId = ref(null)
const deleteUserName = ref('')
const deleting = ref(false)

const defaultForm = () => ({ username: '', email: '', password: '', role_id: null, is_active: true, is_verified: false })
const form = ref(defaultForm())

const loadUsers = async () => {
  loading.value = true; error.value = ''
  try {
    const skip = (currentPage.value - 1) * pageSize
    const [usersRes, rolesRes] = await Promise.all([getUsers(skip, pageSize, searchQuery.value), getRoles()])
    users.value = usersRes.data.users; total.value = usersRes.data.total; roles.value = rolesRes.data
  } catch (err) { error.value = getApiError(err, 'Failed to load data') }
  finally { loading.value = false }
}

const goToPage = (page) => {
  selectedIds.value = new Set()
  currentPage.value = page
  loadUsers()
}

const onSearch = (val) => {
  selectedIds.value = new Set()
  searchQuery.value = val
  currentPage.value = 1
  loadUsers()
}

const openCreate = () => { editingUserId.value = null; form.value = defaultForm(); showModal.value = true }

const openEdit = (user) => {
  editingUserId.value = user.user_id
  const currentRole = user.roles && user.roles.length > 0 ? user.roles[0].role : null
  form.value = {
    username: user.username || '', email: user.email || '', password: '',
    role_id: currentRole ? currentRole.role_id : null,
    is_active: user.is_active ?? true, is_verified: user.is_verified ?? false,
  }
  showModal.value = true
}

const closeModal = () => { showModal.value = false; editingUserId.value = null }

const buildCreatePayload = () => ({ ...pick(form.value, ['username', 'email', 'password', 'is_active', 'is_verified']) })
const buildUpdatePayload = () => {
  const payload = pick(form.value, ['username', 'email', 'is_active', 'is_verified'])
  if (form.value.password && form.value.password.trim()) { payload.password = form.value.password }
  return payload
}

const saveUser = async () => {
  saving.value = true; error.value = ''
  try {
    let userId = editingUserId.value
    if (userId) { await updateUser(userId, buildUpdatePayload()) }
    else { const res = await createUser(buildCreatePayload()); userId = res.data.user_id }
    const originalUser = users.value.find(u => u.user_id === userId)
    const oldRole = originalUser?.roles?.[0]?.role
    const newRoleId = form.value.role_id
    if (newRoleId) {
      if (oldRole && oldRole.role_id !== newRoleId) { try { await removeRole(userId, oldRole.role_id) } catch (e) { console.warn('Failed to remove old role', e) } }
      if (!oldRole || oldRole.role_id !== newRoleId) { await assignRole(userId, newRoleId) }
    } else { if (oldRole) { await removeRole(userId, oldRole.role_id) } }
    closeModal(); currentPage.value = 1; await loadUsers()
  } catch (err) { error.value = getApiError(err, 'Failed to save user') }
  finally { saving.value = false }
}

const confirmDeleteUser = (userId, username) => {
  deletingUserId.value = userId
  deleteUserName.value = username
  showDeleteDialog.value = true
}

const executeDeleteUser = async () => {
  deleting.value = true
  try {
    await deleteUser(deletingUserId.value)
    showDeleteDialog.value = false
    currentPage.value = 1
    await loadUsers()
    toast.success('User deleted successfully')
  } catch (err) {
    toast.error(getApiError(err, 'Failed to delete user'))
    showDeleteDialog.value = false
  } finally {
    deleting.value = false
  }
}


const bulkDeleting = ref(false)
const showBulkDeleteDialog = ref(false)
const deleteSelectedUsers = async () => {
  bulkDeleting.value = true
  showBulkDeleteDialog.value = false
  const ids = [...selectedIds.value]
  let successCount = 0
  let failCount = 0
  for (const id of ids) {
    try {
      await deleteUser(id)
      successCount++
    } catch {
      failCount++
    }
  }
  selectedIds.value = new Set()
  currentPage.value = 1
  await loadUsers()
  if (failCount > 0) {
    toast.warning(`Deleted ${successCount} user(s), ${failCount} failed`)
  } else {
    toast.success(`Deleted ${successCount} user(s)`)
  }
  bulkDeleting.value = false
}
onMounted(loadUsers)
</script>

<template>
  <div>
    <div class="admin-page-header">
      <h1>Users</h1>
      <button class="admin-btn-add" @click="openCreate">+ Add User</button>
    </div>

    <div v-if="error" class="admin-error">{{ error }}</div>
    <div v-if="loading" class="admin-loading">Loading users...</div>

    <div v-else class="admin-table-card">
      <div class="px-4 pt-3 pb-2 border-b border-border-light">
        <SearchFilter v-model="searchQuery" @search="onSearch" placeholder="Search users..." />
      </div>
      <div class="admin-record-count">{{ total }} user(s)</div>
      <div v-if="selectedIds.size > 0" class="admin-bulk-actions">
        <span class="bulk-count">{{ selectedIds.size }} selected</span>
        <button class="admin-btn-delete-selected" :disabled="bulkDeleting" @click="showBulkDeleteDialog = true">
          {{ bulkDeleting ? 'Deleting...' : 'Delete Selected' }}
        </button>
      </div>
      <table class="admin-table">
        <thead>
          <tr>
            <th class="th-checkbox">
              <input type="checkbox" :checked="users.length > 0 && selectedIds.size === users.length" @change="selectAll" />
            </th>
            <th>Username</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Verified</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.user_id" :class="{ 'row-selected': selectedIds.has(user.user_id) }">
            <td class="td-checkbox">
              <input type="checkbox" :checked="selectedIds.has(user.user_id)" @change="toggleSelect(user.user_id)" />
            </td>
            <td class="cell-primary">{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>{{ user.roles && user.roles.length > 0 ? user.roles[0].role?.role_name : 'None' }}</td>
            <td>
              <span class="admin-badge" :class="user.is_active ? 'admin-badge-active' : 'admin-badge-inactive'">
                {{ user.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td>
              <span :class="user.is_verified ? 'text-success' : 'text-ink-muted'" class="text-sm">
                {{ user.is_verified ? 'Yes' : 'No' }}
              </span>
            </td>
            <td>
              <button class="admin-action-btn admin-action-edit" @click="openEdit(user)">Edit</button>
              <button class="admin-action-btn admin-action-delete" @click="confirmDeleteUser(user.user_id, user.username)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <Pagination :current-page="currentPage" :total-items="total" :page-size="pageSize" @page-change="goToPage" />
    </div>

    <div v-if="showModal" class="admin-modal-overlay">
      <div class="admin-modal admin-modal-md">
        <h2>{{ editingUserId ? 'Edit User' : 'Create User' }}</h2>
        <form class="admin-form-grid" @submit.prevent="saveUser">
          <div><label class="form-label">Username</label><input v-model="form.username" required /></div>
          <div><label class="form-label">Email</label><input v-model="form.email" type="email" required /></div>
          <div class="col-span-full">
            <label class="form-label">Role</label>
            <select v-model="form.role_id">
              <option :value="null">No Role</option>
              <option v-for="role in roles" :key="role.role_id" :value="role.role_id">{{ role.role_name }}</option>
            </select>
          </div>
          <div class="col-span-full">
            <label class="form-label">Password <span v-if="editingUserId" class="text-ink-muted">(leave blank to keep
                current)</span></label>
            <input v-model="form.password" type="password" :required="!editingUserId" minlength="8" />
          </div>
          <label class="admin-checkbox-row"><input v-model="form.is_active" type="checkbox" /> Active</label>
          <label class="admin-checkbox-row"><input v-model="form.is_verified" type="checkbox" /> Verified</label>
          <div class="admin-form-actions">
            <button type="button" class="admin-btn-cancel" @click="closeModal">Cancel</button>
            <button :disabled="saving" type="submit" class="admin-btn-save">{{ saving ? 'Saving...' : 'Save' }}</button>
          </div>
        </form>
      </div>
    </div>

    <ConfirmDeleteDialog
      :show="showDeleteDialog"
      title="Delete User"
      :item-name="deleteUserName"
      :deleting="deleting"
      @confirm="executeDeleteUser"
      @cancel="showDeleteDialog = false"
    />

    <div v-if="showBulkDeleteDialog" class="admin-modal-overlay" @click.self="showBulkDeleteDialog = false">
      <div class="admin-modal admin-modal-sm">
        <h2>Delete {{ selectedIds.size }} User(s)</h2>
        <p class="text-ink-muted mb-4">Are you sure you want to delete {{ selectedIds.size }} selected user(s)? This action cannot be undone. All associated data will also be permanently deleted.</p>
        <div class="admin-form-actions">
          <button type="button" class="admin-btn-cancel" @click="showBulkDeleteDialog = false">Cancel</button>
          <button :disabled="bulkDeleting" class="admin-btn-delete-selected" @click="deleteSelectedUsers">
            {{ bulkDeleting ? 'Deleting...' : 'Delete All' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.th-checkbox, .td-checkbox {
  width: 40px;
  text-align: center;
  vertical-align: middle;
}
.th-checkbox input, .td-checkbox input {
  width: 16px;
  height: 16px;
  cursor: pointer;
}
.row-selected {
  background-color: rgba(59, 130, 246, 0.05);
}
.admin-bulk-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: #fef2f2;
  border-bottom: 1px solid #fecaca;
}
.bulk-count {
  font-size: 14px;
  font-weight: 600;
  color: #b91c1c;
}
.admin-btn-delete-selected {
  padding: 6px 16px;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.admin-btn-delete-selected:hover:not(:disabled) {
  background: #b91c1c;
}
.admin-btn-delete-selected:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
