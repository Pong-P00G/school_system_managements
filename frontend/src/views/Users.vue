<script setup>
import { onMounted, ref } from 'vue'
import { createUser, deleteUser, getUsers, updateUser, getRoles, assignRole, removeRole } from '../services/api'
import { getApiError, pick } from '../components/utils/crud'

const users = ref([])
const roles = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingUserId = ref(null)

const defaultForm = () => ({ username: '', email: '', password: '', role_id: null, is_active: true, is_verified: false })
const form = ref(defaultForm())

const loadUsers = async () => {
  loading.value = true; error.value = ''
  try {
    const [usersRes, rolesRes] = await Promise.all([getUsers(0, 1000), getRoles()])
    users.value = usersRes.data.users; total.value = usersRes.data.total; roles.value = rolesRes.data
  } catch (err) { error.value = getApiError(err, 'Failed to load data') }
  finally { loading.value = false }
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
    closeModal(); await loadUsers()
  } catch (err) { error.value = getApiError(err, 'Failed to save user') }
  finally { saving.value = false }
}

const removeUser = async (userId) => {
  if (!confirm('Deactivate this user?')) return
  error.value = ''
  try { await deleteUser(userId); await loadUsers() }
  catch (err) { error.value = getApiError(err, 'Failed to delete user') }
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
      <div class="admin-record-count">{{ total }} user(s)</div>
      <table class="admin-table">
        <thead>
          <tr>
            <th>Username</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Verified</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.user_id">
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
              <button class="admin-action-btn admin-action-delete" @click="removeUser(user.user_id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
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
  </div>
</template>
