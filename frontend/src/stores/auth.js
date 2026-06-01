import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, register as apiRegister } from '../services/api'
import api from '../services/api'

export const useAuthStore = defineStore('auth', () => {
    const user = ref(JSON.parse(localStorage.getItem('user')) || null)

    const isAuthenticated = computed(() => !!user.value)

    const userRole = computed(() => {
        if (!user.value) return null
        const roles = user.value.roles || user.value.role_assignments || []
        if (roles.length === 0) return null
        // Prefer super-admin > admin over first-in-array
        const roleNames = roles.filter(r => r.is_active !== false).map(r => r.role?.role_name?.toLowerCase())
        if (roleNames.includes('super-admin')) return 'super-admin'
        if (roleNames.includes('admin')) return 'admin'
        const first = roleNames[0]
        if (first === 'faculty' || first === 'professor') return 'teacher'
        return first || null
    })

    const isAdmin = computed(() => userRole.value === 'admin' || userRole.value === 'super-admin')
    const isTeacher = computed(() => ['teacher', 'faculty', 'professor'].includes(userRole.value))
    const isStudent = computed(() => userRole.value === 'student')

    async function login(username, password) {
        // Cookie is set by the server; just fetch user profile after login
        await apiLogin(username, password)
        const userResponse = await api.get('/users/me')
        user.value = userResponse.data
        localStorage.setItem('user', JSON.stringify(user.value))
        return true
    }

    async function logout() {
        await api.post('/auth/logout').catch(() => {})
        user.value = null
        localStorage.removeItem('user')
    }

    async function initialize() {
        if (user.value) {
            // Verify session is still valid
            try {
                const res = await api.get('/users/me')
                user.value = res.data
                localStorage.setItem('user', JSON.stringify(user.value))
            } catch {
                user.value = null
                localStorage.removeItem('user')
            }
        }
    }

    return { user, isAuthenticated, userRole, isAdmin, isTeacher, isStudent, login, logout, initialize }
})
