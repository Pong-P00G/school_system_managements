<script setup>
import { onMounted, ref, computed, watch } from 'vue'
import { getPrograms, updateProgram } from '../../services/api'
import { getApiError } from '../../components/utils/crud'

const programs = ref([])
const totalRecords = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showModal = ref(false)
const editingProgramId = ref(null)

const form = ref({
    program_code: '',
    program_name: '',
    program_fee: 0,
    fee_per_year: 0,
    duration_years: 0,
})

// Auto-calculate total when fee_per_year or duration changes
// We use a watcher or computed. 
// However, since we want to allow manual override of total, we should probably just update it when inputs change, 
// but not force it if user manually edits total? 
// The user request "fix program fee" implies they want the calculation working.
// I'll make it so changing per_year or duration updates program_fee.
watch(() => [form.value.fee_per_year, form.value.duration_years], ([newFee, newDuration]) => {
    form.value.program_fee = (Number(newFee) || 0) * (Number(newDuration) || 0)
})

const loadPrograms = async () => {
    loading.value = true
    error.value = ''
    try {
        const response = await getPrograms(0, 1000)
        programs.value = response.data.programs
        totalRecords.value = response.data.total
    } catch (err) {
        error.value = getApiError(err, 'Failed to load programs')
    } finally {
        loading.value = false
    }
}

const openEdit = (program) => {
    editingProgramId.value = program.program_id
    form.value = {
        program_code: program.program_code,
        program_name: program.program_name,
        program_fee: Number(program.program_fee || 0),
        fee_per_year: Number(program.fee_per_year || 0),
        duration_years: Number(program.duration_years || 0),
    }
    showModal.value = true
}

const closeModal = () => {
    showModal.value = false
    editingProgramId.value = null
}

const saveFee = async () => {
    saving.value = true
    error.value = ''
    try {
        await updateProgram(editingProgramId.value, {
            program_fee: Number(form.value.program_fee),
            fee_per_year: Number(form.value.fee_per_year),
            duration_years: Number(form.value.duration_years)
        })
        closeModal()
        await loadPrograms()
    } catch (err) {
        error.value = getApiError(err, 'Failed to update fee')
    } finally {
        saving.value = false
    }
}

onMounted(loadPrograms)
</script>

<template>
    <div>
        <div class="mb-6 flex items-center justify-between">
            <h1 class="text-2xl font-bold text-slate-800">Program Fees</h1>
        </div>

        <div v-if="error" class="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
            {{ error }}
        </div>

        <div v-if="loading" class="rounded-lg bg-white p-6 text-slate-500">
            Loading programs...
        </div>

        <div v-else class="overflow-hidden rounded-lg bg-white shadow">
            <div class="border-b bg-gray-50 px-6 py-3 text-sm text-gray-500">
                {{ totalRecords }} program(s)
            </div>
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Code</th>
                        <th class="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Name</th>
                        <th class="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Degree</th>
                        <th class="px-6 py-3 text-right text-xs font-medium uppercase text-gray-500">Duration</th>
                        <th class="px-6 py-3 text-right text-xs font-medium uppercase text-gray-500">Fee/Year</th>
                        <th class="px-6 py-3 text-right text-xs font-medium uppercase text-gray-500">Total Fee</th>
                        <th class="px-6 py-3 text-center text-xs font-medium uppercase text-gray-500">Actions</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 bg-white">
                    <tr v-for="program in programs" :key="program.program_id">
                        <td class="px-6 py-4 text-sm font-medium text-indigo-700">{{ program.program_code }}</td>
                        <td class="px-6 py-4 text-sm text-slate-800">{{ program.program_name }}</td>
                        <td class="px-6 py-4 text-sm text-slate-600">{{ program.degree_level }}</td>
                        <td class="px-6 py-4 text-sm text-right text-slate-600">{{ Number(program.duration_years || 0)
                            }} Years</td>
                        <td class="px-6 py-4 text-sm text-right font-medium text-slate-900">${{
                            Number(program.fee_per_year || 0).toLocaleString('en-US', {minimumFractionDigits: 2}) }}
                        </td>
                        <td class="px-6 py-4 text-sm text-right font-bold text-slate-900">${{ Number(program.program_fee || 0).toLocaleString('en-US', {minimumFractionDigits: 2}) }}</td>
                        <td class="px-6 py-4 text-sm text-center">
                            <button class="text-indigo-600 hover:text-indigo-800 font-medium"
                                @click="openEdit(program)">Edit Fees</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div class="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
                <h2 class="mb-4 text-xl font-bold text-slate-800">Edit Program Fee</h2>
                <form @submit.prevent="saveFee">
                    <div class="mb-4 bg-slate-50 p-3 rounded-md border border-slate-100">
                        <div class="flex flex-col">
                            <span class="text-xs text-slate-500 uppercase font-semibold">Program</span>
                            <span class="font-medium text-slate-900">{{ form.program_name }}</span>
                            <span class="text-xs text-slate-500">{{ form.program_code }}</span>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div class="col-span-1">
                            <label class="mb-1 block text-sm font-medium">Duration (Years)</label>
                            <input v-model.number="form.duration_years" type="number" min="0" step="0.5"
                                class="w-full rounded-md border px-3 py-2" required />
                        </div>
                        <div class="col-span-1">
                            <label class="mb-1 block text-sm font-medium">Fee Per Year</label>
                            <div class="relative">
                                <span class="absolute left-3 top-2 text-slate-500">$</span>
                                <input v-model.number="form.fee_per_year" type="number" min="0" step="0.01"
                                    class="w-full rounded-md border pl-8 pr-3 py-2" required />
                            </div>
                        </div>
                    </div>

                    <div class="mb-6">
                        <label class="mb-1 block text-sm font-medium">Total Program Fee</label>
                        <div class="relative">
                            <span class="absolute left-3 top-2 text-slate-500">$</span>
                            <input v-model.number="form.program_fee" type="number" min="0" step="0.01"
                                class="w-full rounded-md border pl-8 pr-3 py-2 bg-slate-50 font-bold text-slate-800"
                                required />
                        </div>
                        <p class="text-xs text-slate-500 mt-1">Automatically calculated as Duration × Fee/Year. Can be
                            adjusted manually.</p>
                    </div>

                    <div class="flex justify-end gap-3">
                        <button type="button" class="rounded-md border px-4 py-2" @click="closeModal">Cancel</button>
                        <button :disabled="saving" type="submit"
                            class="rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700 disabled:opacity-60">
                            {{ saving ? 'Saving...' : 'Save' }}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</template>
