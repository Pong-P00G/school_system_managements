<script setup>
import { onMounted, ref } from 'vue'
import { createDepartment, deleteDepartment, getDepartmentCourses, getDepartmentPrograms, getDepartments, updateDepartment } from '../services/api'
import { getApiError, pick, toDateInput, toNullableInt, toNullableString } from '../components/utils/crud'
import { useToast } from '../composables/useToast'
import Pagination from '../components/Pagination.vue'
import SearchFilter from '../components/SearchFilter.vue'
import ConfirmDeleteDialog from '../components/ConfirmDeleteDialog.vue'

const toast = useToast()

const departments = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingDepartmentId = ref(null)
const currentPage = ref(1)
const pageSize = 100
const searchQuery = ref('')

const showDeleteDialog = ref(false)
const deletingDeptId = ref(null)
const deleteDeptName = ref('')
const deleteDependencies = ref([])
const checkingDeps = ref(false)
const deleting = ref(false)

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
    const skip = (currentPage.value - 1) * pageSize
    const response = await getDepartments(skip, pageSize, searchQuery.value)
    departments.value = response.data.departments
    total.value = response.data.total
  } catch (err) {
    error.value = getApiError(err, 'Failed to load departments')
  } finally {
    loading.value = false
  }
}

const goToPage = (page) => {
  currentPage.value = page
  loadDepartments()
}

const onSearch = (val) => {
  searchQuery.value = val
  currentPage.value = 1
  loadDepartments()
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
    currentPage.value = 1
    await loadDepartments()
  } catch (err) {
    error.value = getApiError(err, 'Failed to save department')
  } finally {
    saving.value = false
  }
}

const confirmDeleteDepartment = async (departmentId, deptName) => {
  deletingDeptId.value = departmentId
  deleteDeptName.value = deptName
  deleteDependencies.value = []
  checkingDeps.value = true
  showDeleteDialog.value = true

  try {
    const [coursesRes, programsRes] = await Promise.all([
      getDepartmentCourses(departmentId),
      getDepartmentPrograms(departmentId),
    ])
    const deps = []
    if (coursesRes.data?.total || coursesRes.data?.courses?.length) {
      const count = coursesRes.data.total ?? coursesRes.data.courses.length
      deps.push(`${count} course(s) assigned to this department`)
    }
    if (programsRes.data?.total || programsRes.data?.programs?.length) {
      const count = programsRes.data.total ?? programsRes.data.programs.length
      deps.push(`${count} program(s) belong to this department`)
    }
    deleteDependencies.value = deps
  } catch (err) {
    console.warn('Failed to check dependencies', err)
  } finally {
    checkingDeps.value = false
  }
}

const executeDeleteDepartment = async () => {
  deleting.value = true
  try {
    await deleteDepartment(deletingDeptId.value)
    showDeleteDialog.value = false
    currentPage.value = 1
    await loadDepartments()
    toast.success('Department deleted successfully')
  } catch (err) {
    toast.error(getApiError(err, 'Failed to delete department'))
    showDeleteDialog.value = false
  } finally {
    deleting.value = false
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
      <div class="px-4 pt-3 pb-2 border-b border-border-light">
        <SearchFilter v-model="searchQuery" @search="onSearch" placeholder="Search departments..." />
      </div>
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
                @click="confirmDeleteDepartment(dept.department_id, dept.department_name)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <Pagination :current-page="currentPage" :total-items="total" :page-size="pageSize" @page-change="goToPage" />
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

    <ConfirmDeleteDialog
      :show="showDeleteDialog"
      title="Delete Department"
      :item-name="deleteDeptName"
      :dependencies="deleteDependencies"
      :loading="checkingDeps"
      :deleting="deleting"
      @confirm="executeDeleteDepartment"
      @cancel="showDeleteDialog = false"
    />
  </div>
</template>
