<script setup>
import { onMounted, ref } from 'vue'
import { createProgram, deleteProgram, getDepartments, getPrograms, getProgramStudents, updateProgram } from '../services/api'
import { getApiError, pick, toNullableString } from '../components/utils/crud'
import { useToast } from '../composables/useToast'
import Pagination from '../components/Pagination.vue'
import SearchFilter from '../components/SearchFilter.vue'
import ConfirmDeleteDialog from '../components/ConfirmDeleteDialog.vue'

const toast = useToast()

const programs = ref([])
const departments = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingProgramId = ref(null)
const currentPage = ref(1)
const pageSize = 100
const searchQuery = ref('')

const showDeleteDialog = ref(false)
const deletingProgramId = ref(null)
const deleteProgramName = ref('')
const deleteDependencies = ref([])
const checkingDeps = ref(false)
const deleting = ref(false)

const defaultForm = () => ({
  program_code: '',
  program_name: '',
  department_id: '',
  degree_level: 'Bachelor',
  duration_years: 4,
  total_credits_required: 120,
  description: '',
  coordinator_id: '',
  accreditation_status: '',
  accreditation_body: '',
  is_active: true,
})

const form = ref(defaultForm())

const loadPrograms = async () => {
  loading.value = true
  error.value = ''
  try {
    const skip = (currentPage.value - 1) * pageSize
    const [programsRes, departmentsRes] = await Promise.all([getPrograms(skip, pageSize, null, null, searchQuery.value), getDepartments(0, 200)])
    programs.value = programsRes.data.programs
    total.value = programsRes.data.total
    departments.value = departmentsRes.data.departments
  } catch (err) {
    error.value = getApiError(err, 'Failed to load programs')
  } finally {
    loading.value = false
  }
}

const goToPage = (page) => {
  currentPage.value = page
  loadPrograms()
}

const onSearch = (val) => {
  searchQuery.value = val
  currentPage.value = 1
  loadPrograms()
}

const openCreate = () => {
  editingProgramId.value = null
  form.value = defaultForm()
  showModal.value = true
}

const openEdit = (program) => {
  editingProgramId.value = program.program_id
  form.value = {
    program_code: program.program_code || '',
    program_name: program.program_name || '',
    department_id: String(program.department_id || ''),
    degree_level: program.degree_level || 'Bachelor',
    duration_years: Number(program.duration_years || 4),
    total_credits_required: Number(program.total_credits_required || 120),
    description: program.description || '',
    coordinator_id: program.coordinator_id || '',
    accreditation_status: program.accreditation_status || '',
    accreditation_body: program.accreditation_body || '',
    is_active: program.is_active ?? true,
  }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingProgramId.value = null
}

const buildPayload = () => ({
  ...pick(form.value, ['program_code', 'program_name', 'degree_level', 'is_active']),
  department_id: Number(form.value.department_id),
  duration_years: Number(form.value.duration_years),
  total_credits_required: Number(form.value.total_credits_required),
  description: toNullableString(form.value.description),
  coordinator_id: toNullableString(form.value.coordinator_id),
  accreditation_status: toNullableString(form.value.accreditation_status),
  accreditation_body: toNullableString(form.value.accreditation_body),
})

const saveProgram = async () => {
  saving.value = true
  error.value = ''
  try {
    const payload = buildPayload()
    if (editingProgramId.value) {
      await updateProgram(editingProgramId.value, payload)
    } else {
      await createProgram(payload)
    }
    closeModal()
    currentPage.value = 1
    await loadPrograms()
  } catch (err) {
    error.value = getApiError(err, 'Failed to save program')
  } finally {
    saving.value = false
  }
}

const confirmDeleteProgram = async (programId, programName) => {
  deletingProgramId.value = programId
  deleteProgramName.value = programName
  deleteDependencies.value = []
  checkingDeps.value = true
  showDeleteDialog.value = true

  try {
    const res = await getProgramStudents(programId)
    const students = res.data?.students || []
    if (students.length > 0) {
      deleteDependencies.value = [`${students.length} student(s) are enrolled in this program`]
    }
  } catch (err) {
    console.warn('Failed to check dependencies', err)
  } finally {
    checkingDeps.value = false
  }
}

const executeDeleteProgram = async () => {
  deleting.value = true
  try {
    await deleteProgram(deletingProgramId.value)
    showDeleteDialog.value = false
    currentPage.value = 1
    await loadPrograms()
    toast.success('Program deleted successfully')
  } catch (err) {
    toast.error(getApiError(err, 'Failed to delete program'))
    showDeleteDialog.value = false
  } finally {
    deleting.value = false
  }
}

const departmentNameById = (departmentId) => {
  const match = departments.value.find((department) => department.department_id === departmentId)
  return match ? match.department_name : `ID ${departmentId}`
}

onMounted(loadPrograms)
</script>

<template>
  <div>
    <div class="admin-page-header">
      <h1>Programs</h1>
      <button class="admin-btn-add" @click="openCreate">+ Add Program</button>
    </div>

    <div v-if="error" class="admin-error">{{ error }}</div>
    <div v-if="loading" class="admin-loading">Loading programs...</div>

    <div v-else class="admin-table-card">
      <div class="px-4 pt-3 pb-2 border-b border-border-light">
        <SearchFilter v-model="searchQuery" @search="onSearch" placeholder="Search programs..." />
      </div>
      <div class="admin-record-count">{{ total }} program(s)</div>
      <table class="admin-table">
        <thead>
          <tr>
            <th>Code</th>
            <th>Name</th>
            <th>Department</th>
            <th>Degree</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="program in programs" :key="program.program_id">
            <td class="cell-primary">{{ program.program_code }}</td>
            <td class="font-medium text-ink">{{ program.program_name }}</td>
            <td>{{ departmentNameById(program.department_id) }}</td>
            <td>{{ program.degree_level }}</td>
            <td>
              <span class="admin-badge" :class="program.is_active ? 'admin-badge-active' : 'admin-badge-inactive'">
                {{ program.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td>
              <button class="admin-action-btn admin-action-edit" @click="openEdit(program)">Edit</button>
              <button class="admin-action-btn admin-action-delete"
                @click="confirmDeleteProgram(program.program_id, program.program_name)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <Pagination :current-page="currentPage" :total-items="total" :page-size="pageSize" @page-change="goToPage" />
    </div>

    <div v-if="showModal" class="admin-modal-overlay">
      <div class="admin-modal admin-modal-lg">
        <h2>{{ editingProgramId ? 'Edit Program' : 'Create Program' }}</h2>
        <form class="admin-form-grid" @submit.prevent="saveProgram">
          <div><label class="form-label">Program Code</label><input v-model="form.program_code" required /></div>
          <div><label class="form-label">Program Name</label><input v-model="form.program_name" required /></div>
          <div>
            <label class="form-label">Department</label>
            <select v-model="form.department_id" required>
              <option value="" disabled>Select department</option>
              <option v-for="department in departments" :key="department.department_id"
                :value="String(department.department_id)">
                {{ department.department_code }} - {{ department.department_name }}
              </option>
            </select>
          </div>
          <div>
            <label class="form-label">Degree Level</label>
            <select v-model="form.degree_level">
              <option value="Certificate">Certificate</option>
              <option value="Associate">Associate</option>
              <option value="Bachelor">Bachelor</option>
              <option value="Master">Master</option>
              <option value="Doctorate">Doctorate</option>
            </select>
          </div>
          <div><label class="form-label">Duration (Years)</label><input v-model.number="form.duration_years"
              type="number" step="0.5" min="1" /></div>
          <div><label class="form-label">Total Credits Required</label><input
              v-model.number="form.total_credits_required" type="number" min="1" required /></div>
          <div><label class="form-label">Coordinator ID</label><input v-model="form.coordinator_id" /></div>
          <div><label class="form-label">Accreditation Status</label><input v-model="form.accreditation_status" /></div>
          <div class="col-span-full"><label class="form-label">Accreditation Body</label><input
              v-model="form.accreditation_body" /></div>
          <div class="col-span-full"><label class="form-label">Description</label><textarea v-model="form.description"
              rows="3" /></div>
          <label class="admin-checkbox-row"><input v-model="form.is_active" type="checkbox" /> Active</label>
          <div class="admin-form-actions">
            <button type="button" class="admin-btn-cancel" @click="closeModal">Cancel</button>
            <button :disabled="saving" type="submit" class="admin-btn-save">{{ saving ? 'Saving...' : 'Save' }}</button>
          </div>
        </form>
      </div>
    </div>

    <ConfirmDeleteDialog
      :show="showDeleteDialog"
      title="Delete Program"
      :item-name="deleteProgramName"
      :dependencies="deleteDependencies"
      :loading="checkingDeps"
      :deleting="deleting"
      @confirm="executeDeleteProgram"
      @cancel="showDeleteDialog = false"
    />
  </div>
</template>
