<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Icons from '../components/icon/Icons.vue'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const userRole = computed(() => authStore.userRole)
const mobileOpen = ref(false)

const userName = computed(() => {
    const user = authStore.user || JSON.parse(localStorage.getItem('user') || '{}')
    return user.username || 'User'
})

const userInitial = computed(() => userName.value.charAt(0).toUpperCase())

const navigationItems = computed(() => {
    if (userRole.value === 'student') {
        return [
            { name: 'Dashboard', path: '/student/dashboard', icons: 'mdi-view-dashboard' },
            { name: 'Courses', path: '/student/courses', icons: 'mdi-book-open-variant' },
            { name: 'Assignments', path: '/student/assignments', icons: 'mdi-file-document' },
            { name: 'Grades', path: '/student/grades', icons: 'mdi-chart-line' },
            { name: 'Schedule', path: '/student/schedule', icons: 'mdi-calendar' },
        ]
    } else if (userRole.value === 'teacher') {
        return [
            { name: 'Dashboard', path: '/teacher/dashboard', icons: 'mdi-view-dashboard' },
            { name: 'My Classes', path: '/teacher/courses', icons: 'mdi-book-open-variant' },
            { name: 'Students', path: '/teacher/students', icons: 'mdi-account-group' },
            { name: 'Grading', path: '/teacher/grades', icons: 'mdi-chart-line' },
        ]
    }
    return []
})

const logout = async () => {
    await authStore.logout()
    router.push('/login')
}

const isActive = (path) => route.path === path
</script>

<template>
    <div class="flex flex-col min-h-screen bg-page font-sans">
        <!-- Navbar -->
        <header class="bg-primary shadow-[0_2px_12px_rgba(0,0,0,0.15)] sticky top-0 z-40">
            <div class="max-w-7xl mx-auto px-4 sm:px-6">
                <div class="flex items-center justify-between h-15">
                    <!-- Left: Logo + Links -->
                    <div class="flex items-center gap-10">
                        <div class="flex items-center gap-2">
                            <div
                                class="w-8 h-8 bg-white/15 rounded-lg flex items-center justify-center text-white text-lg">
                                <Icons name="mdi-school" />
                            </div>
                            <span class="text-lg font-bold text-white tracking-wide">SMS</span>
                        </div>

                        <!-- Desktop Nav -->
                        <nav class="hidden md:flex items-center gap-1">
                            <router-link v-for="item in navigationItems" :key="item.path" :to="item.path"
                                class="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-[0.825rem] font-medium text-white/70 no-underline transition-all duration-200 hover:bg-white/10 hover:text-white"
                                :class="{ 'bg-white/18 text-white!': isActive(item.path) }">
                                <Icons :name="item.icons" class="text-lg" />
                                {{ item.name }}
                            </router-link>
                        </nav>
                    </div>

                    <!-- Right -->
                    <div class="flex items-center gap-4">
                        <div class="hidden md:flex items-center gap-2">
                            <div
                                class="w-8 h-8 rounded-full bg-white/18 text-white font-semibold text-[0.8rem] flex items-center justify-center">
                                {{ userInitial }}
                            </div>
                            <span class="text-[0.825rem] font-medium text-white/85">{{ userName }}</span>
                        </div>
                        <button @click="logout"
                            class="hidden md:flex items-center gap-1.5 px-3 py-1.5 border border-white/20 rounded-lg bg-transparent text-white/80 font-sans text-[0.8rem] font-medium cursor-pointer transition-all duration-200 hover:bg-error/15 hover:border-error/30 hover:text-red-300">
                            <Icons name="mdi-logout" class="text-base" />
                            Logout
                        </button>

                        <!-- Mobile Toggle -->
                        <button @click="mobileOpen = !mobileOpen"
                            class="flex md:hidden items-center justify-center w-9 h-9 border-none rounded-lg bg-white/10 text-white text-xl cursor-pointer">
                            <Icons :name="mobileOpen ? 'mdi-close' : 'mdi-menu'" />
                        </button>
                    </div>
                </div>
            </div>

            <!-- Mobile Menu -->
            <Transition name="slide">
                <div v-if="mobileOpen" class="md:hidden px-4 pb-4 pt-3 border-t border-white/10 flex flex-col gap-1">
                    <router-link v-for="item in navigationItems" :key="item.path" :to="item.path"
                        class="flex items-center gap-2.5 px-4 py-2.5 rounded-lg text-[0.875rem] font-medium text-white/75 no-underline transition-all duration-150 hover:bg-white/12 hover:text-white"
                        :class="{ 'bg-white/12 text-white!': isActive(item.path) }" @click="mobileOpen = false">
                        <Icons :name="item.icons" />
                        {{ item.name }}
                    </router-link>
                    <button @click="logout"
                        class="flex items-center gap-2.5 px-4 py-2.5 rounded-lg text-[0.875rem] font-medium text-red-300 no-underline border-none bg-transparent w-full cursor-pointer font-sans mt-2 border-t border-white/8 pt-4 hover:bg-white/12">
                        <Icons name="mdi-logout" />
                        Logout
                    </button>
                </div>
            </Transition>
        </header>

        <!-- Main Content -->
        <main class="flex-1 py-5 sm:py-8">
            <div class="max-w-7xl mx-auto px-4 sm:px-6">
                <router-view v-slot="{ Component }">
                    <transition name="fade" mode="out-in">
                        <component :is="Component" />
                    </transition>
                </router-view>
            </div>
        </main>

        <!-- Footer -->
        <footer class="py-6 text-center">
            <div class="max-w-7xl mx-auto mb-5 h-px bg-border-light"></div>
            <p class="text-[0.78rem] text-ink-muted m-0">
                &copy; {{ new Date().getFullYear() }} School Management System &middot; All rights reserved
            </p>
        </footer>
    </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
    transition: all 0.25s ease;
    overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
    opacity: 0;
    max-height: 0;
    padding-top: 0;
    padding-bottom: 0;
}

.slide-enter-to,
.slide-leave-from {
    opacity: 1;
    max-height: 400px;
}
</style>
