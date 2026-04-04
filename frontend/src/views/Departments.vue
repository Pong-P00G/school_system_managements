<script setup>
import { onMounted, ref } from 'vue'
import { createDepartment, deleteDepartment, getDepartments, updateDepartment } from '../services/api'
import { getApiError, pick, toDateInput, toNullableInt, toNullableString } from '../components/utils/crud'

const departments = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingDepartmentId = ref(null)

const defaultForm = () => ({
  department_code: '',
  department_name: '',
  description: '',
  head_faculty_id: '',
  parent_department_id: '',
  building: '',
  phone: '',
  email: '',
  website_url: '',
  established_date: '',
  is_active: true,
})

const form = ref(defaultForm())

const loadDepartments = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await getDepartments(0, 200)
    departments.value = response.data.departments
    total.value = response.data.total
  } catch (err) {
    error.value = getApiError(err, 'Failed to load departments')
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editingDepartmentId.value = null
  form.value = defaultForm()
  showModal.value = true
}

const openEdit = (department) => {
  editingDepartmentId.value = department.department_id
  form.value = {
    department_code: department.department_code || '',
    department_name: department.department_name || '',
    description: department.description || '',
    head_faculty_id: department.head_faculty_id || '',
    parent_department_id: department.parent_department_id ?? '',
    building: department.building || '',
    phone: department.phone || '',
    email: department.email || '',
    website_url: department.website_url || '',
    established_date: toDateInput(department.established_date),
    is_active: department.is_active ?? true,
  }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingDepartmentId.value = null
}

const buildPayload = () => ({
  ...pick(form.value, ['department_code', 'department_name', 'is_active']),
  description: toNullableString(form.value.description),
  head_faculty_id: toNullableString(form.value.head_faculty_id),
  parent_department_id: toNullableInt(form.value.parent_department_id),
  building: toNullableString(form.value.building),
  phone: toNullableString(form.value.phone),
  email: toNullableString(form.value.email),
  website_url: toNullableString(form.value.website_url),
  established_date: toNullableString(form.value.established_date),
})

const saveDepartment = async () => {
  saving.value = true
  error.value = ''
  try {
    const payload = buildPayload()
    if (editingDepartmentId.value) {
      await updateDepartment(editingDepartmentId.value, payload)
    } else {
      await createDepartment(payload)
    }
    closeModal()
    await loadDepartments()
  } catch (err) {
    error.value = getApiError(err, 'Failed to save department')
  } finally {
    saving.value = false
  }
}

const removeDepartment = async (departmentId) => {
  if (!confirm('Delete this department?')) return
  error.value = ''
  try {
    await deleteDepartment(departmentId)
    await loadDepartments()
  } catch (err) {
    error.value = getApiError(err, 'Failed to delete department')
  }
}

onMounted(loadDepartments)
</script>

<template>
  <div>
    <div class="admin-page-header">
      <h1>Departments</h1>
      <button class="admin-btn-add" @click="openCreate">+ Add Department</button>
    </div>

    <div v-if="error" class="admin-error">{{ error }}</div>

    <div v-if="loading" class="admin-loading">Loading departments...</div>

    <div v-else class="admin-table-card">
      <div class="admin-record-count">{{ total }} department(s)</div>
      <table class="admin-table">
        <thead>
          <tr>
            <th>Code</th>
            <th>Name</th>
            <th>Building</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="dept in departments" :key="dept.department_id">
            <td class="cell-primary">{{ dept.department_code }}</td>
            <td class="font-medium text-ink">{{ dept.department_name }}</td>
            <td>{{ dept.building || '-' }}</td>
            <td>
              <span class="admin-badge" :class="dept.is_active ? 'admin-badge-active' : 'admin-badge-inactive'">
                {{ dept.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td>
              <button class="admin-action-btn admin-action-edit" @click="openEdit(dept)">Edit</button>
              <button class="admin-action-btn admin-action-delete"
                @click="removeDepartment(dept.department_id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showModal" class="admin-modal-overlay">
      <div class="admin-modal admin-modal-lg">
        <h2>{{ editingDepartmentId ? 'Edit Department' : 'Create Department' }}</h2>
        <form class="admin-form-grid" @submit.prevent="saveDepartment">
          <div>
            <label class="form-label">Department Code</label>
            <input v-model="form.department_code" required />
          </div>
          <div>
            <label class="form-label">Department Name</label>
            <input v-model="form.department_name" required />
          </div>
          <div>
            <label class="form-label">Building</label>
            <input v-model="form.building" />
          </div>
          <div>
            <label class="form-label">Parent Department ID</label>
            <input v-model="form.parent_department_id" type="number" min="1" />
          </div>
          <div>
            <label class="form-label">Email</label>
            <input v-model="form.email" type="email" />
          </div>
          <div>
            <label class="form-label">Phone</label>
            <input v-model="form.phone" />
          </div>
          <div>
            <label class="form-label">Website URL</label>
            <input v-model="form.website_url" />
          </div>
          <div>
            <label class="form-label">Established Date</label>
            <input v-model="form.established_date" type="date" />
          </div>
          <div>
            <label class="form-label">Head Faculty ID</label>
            <input v-model="form.head_faculty_id" />
          </div>
          <label class="admin-checkbox-row">
            <input v-model="form.is_active" type="checkbox" />
            Active
          </label>
          <div class="col-span-full">
            <label class="form-label">Description</label>
            <textarea v-model="form.description" rows="3" />
          </div>
          <div class="admin-form-actions">
            <button type="button" class="admin-btn-cancel" @click="closeModal">Cancel</button>
            <button :disabled="saving" type="submit" class="admin-btn-save">
              {{ saving ? 'Saving...' : 'Save' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
