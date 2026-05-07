import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, register as apiRegister } from '../services/api'
import api from '../services/api'

export const useAuthStore = defineStore('auth', () => {
    const user = ref(JSON.parse(localStorage.getItem('user')) || null)
    const token = ref(localStorage.getItem('access_token') || null)
    
    const isAuthenticated = computed(() => !!token.value)
    
    const userRole = computed(() => {
        if (!user.value || !user.value.roles || user.value.roles.length === 0) return null
        const assignedRole = user.value.roles[0]?.role?.role_name?.toLowerCase()
        if (assignedRole === 'faculty') return 'teacher'
        return assignedRole || null
    })

    const isAdmin = computed(() => userRole.value === 'admin')
    const isTeacher = computed(() => userRole.value === 'teacher' || userRole.value === 'faculty')
    const isStudent = computed(() => userRole.value === 'student')

    async function login(username, password) {
        try {
            const response = await apiLogin(username, password)
            const { access_token, token_type } = response.data
            
            if (access_token) {
                token.value = access_token
                localStorage.setItem('access_token', access_token)
                
                // Fetch user details
                try {
                    const userResponse = await api.get('/users/me')
                    user.value = userResponse.data
                    localStorage.setItem('user', JSON.stringify(user.value))
                } catch (userError) {
                    console.error('Failed to fetch user details:', userError)
                    // Fallback: If login response had user info (depends on backend)
                    if (response.data.user) {
                        user.value = response.data.user
                        localStorage.setItem('user', JSON.stringify(user.value))
                    }
                }
                return true
            }
            return false
        } catch (error) {
            console.error('Login error:', error)
            throw error
        }
    }

    function logout() {
        token.value = null
        user.value = null
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
    }

    function initialize() {
        // Optional: verify token validity on app start
        const storedToken = localStorage.getItem('access_token')
        if (storedToken) {
            token.value = storedToken
            // Could verify with /users/me here
        }
    }

    return {
        user,
        token,
        userRole,
        isAuthenticated,
        isAdmin,
        isTeacher,
        isStudent,
        login,
        logout,
        initialize
    }
})
