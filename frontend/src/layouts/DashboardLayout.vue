<script setup>
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Icons from '../components/icon/Icons.vue'
import NotificationBell from '../components/NotificationBell.vue'

const collapsed = ref(true)
const mobileOpen = ref(false)
const toggleSidebar = () => { collapsed.value = !collapsed.value }
const toggleMobile = () => { mobileOpen.value = !mobileOpen.value }
const closeMobile = () => { mobileOpen.value = false }

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const userName = computed(() => authStore.user?.username || 'Admin', 'Super Admin')
const userEmail = computed(() => authStore.user?.email || '')

const navigationItems = [
    { name: 'Dashboard', path: '/dashboard', Icons: 'LayoutDashboard' },
    { name: 'Departments', path: '/departments', Icons: 'Building2' },
    { name: 'Programs', path: '/programs', Icons: 'GraduationCap' },
    { name: 'Courses', path: '/courses', Icons: 'BookOpen' },
    { name: 'Terms', path: '/terms', Icons: 'Calendar' },
    { name: 'Enrollments', path: '/enrollments', Icons: 'ClipboardCheck' },
    { name: 'Sections', path: '/sections', Icons: 'Layers' },
    { name: 'Users', path: '/users', Icons: 'Users' },
    { name: 'Lecturers', path: '/lecturer', Icons: 'Users' },
    { name: 'Students', path: '/students', Icons: 'UserSquare' },
    { name: 'Staff', path: '/staff', Icons: 'Briefcase' },
    { name: 'Finance', path: '/admin/finance/program-fees', Icons: 'Banknote' },
    { name: 'Notifications', path: '/notifications', Icons: 'Bell' },
    { name: 'Attendance', path: '/attendance', Icons: 'CalendarCheck' },
    { name: 'Roles', path: '/roles', Icons: 'Shield' },
    { name: 'Permissions', path: '/permissions', Icons: 'Lock' },
]

const logout = async () => {
    await authStore.logout()
    router.push('/login')
}

const isActive = (path) => route.path === path

const navigateTo = (path) => {
    closeMobile()
    router.push(path)
}
</script>

<template>
    <div class="min-h-screen flex bg-page">
        <!-- Mobile overlay -->
        <transition name="fade-overlay">
            <div v-if="mobileOpen" class="fixed inset-0 z-30 bg-black/30 backdrop-blur-sm lg:hidden"
                @click="closeMobile" />
        </transition>

        <!-- Sidebar -->
        <aside
            class="fixed inset-y-0 left-0 z-40 flex flex-col bg-surface border-r border-border-light transition-all duration-250 ease-in-out"
            :class="[
                mobileOpen ? 'translate-x-0 w-60' : '-translate-x-full w-60',
                'lg:translate-x-0',
                collapsed ? 'lg:w-18' : 'lg:w-60'
            ]">
            <!-- Logo area -->
            <div class="flex items-center gap-3 px-4 py-5 border-b border-border-light"
                :class="{ 'lg:justify-center': collapsed } && { 'md:h-20': collapsed && !mobileOpen }">
                <div @click="toggleSidebar"
                    class="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0 cursor-pointer"
                    title="Toggle sidebar">
                    <span class="text-base font-bold text-white">S</span>
                </div>
                <transition name="fade-text">
                    <div v-if="!collapsed || mobileOpen" class="overflow-hidden whitespace-nowrap"
                        :class="{ 'lg:hidden': collapsed && !mobileOpen }">
                        <h1 class="text-base font-semibold text-ink">
                            Admin<span class="text-primary">SMS</span>
                        </h1>
                        <p class="text-[10px] uppercase tracking-widest text-ink-muted font-medium">Management</p>
                    </div>
                </transition>
                <!-- Close button (mobile only) -->
                <button @click="closeMobile" class="ml-auto lg:hidden p-1 rounded-md hover:bg-page text-ink-muted">
                    <Icons name="X" class="w-5 h-5" />
                </button>
            </div>

            <!-- Navigation -->
            <nav class="flex-1 overflow-y-auto px-2 py-2 flex flex-col gap-0.5 [scrollbar-width:thin]">
                <router-link v-for="item in navigationItems" :key="item.path" :to="item.path"
                    class="flex items-center gap-[0.65rem] px-3 py-[0.55rem] rounded-lg text-ink-secondary no-underline text-[0.85rem] font-[450] transition-all duration-150 ease-in-out whitespace-nowrap hover:bg-sidebar-hover hover:text-ink"
                    :class="[isActive(item.path) ? 'bg-sidebar-active text-primary font-[550] hover:bg-primary-100' : '', collapsed && !mobileOpen ? 'lg:justify-center' : '']"
                    :title="collapsed ? item.name : ''" @click="closeMobile">
                    <Icons :name="item.Icons" class="w-4 h-4 shrink-0" />
                    <transition name="fade-text">
                        <span v-if="!collapsed || mobileOpen" class="overflow-hidden"
                            :class="{ 'lg:hidden': collapsed && !mobileOpen }">{{ item.name }}</span>
                    </transition>
                </router-link>
            </nav>

            <!-- User section -->
            <div class="flex items-center gap-[0.65rem] p-3 m-2 border-t border-border-light">
                <div
                    class="w-8 h-8 rounded-full bg-primary-50 text-primary flex items-center justify-center text-[0.8rem] font-semibold shrink-0">
                    {{ userName.charAt(0).toUpperCase() }}
                </div>
                <transition name="fade-text">
                    <div v-if="!collapsed || mobileOpen" class="flex-1 min-w-0"
                        :class="{ 'lg:hidden': collapsed && !mobileOpen }">
                        <p class="text-sm font-medium text-ink truncate">{{ userName }}</p>
                        <p class="text-xs text-ink-muted truncate">{{ userEmail }}</p>
                    </div>
                </transition>
                <transition name="fade-text">
                    <button v-if="!collapsed || mobileOpen" @click="logout"
                        class="flex items-center justify-center p-[0.35rem] rounded-md border-none bg-transparent text-ink-muted cursor-pointer transition-all duration-150 ease-in-out shrink-0 hover:bg-error-light hover:text-error"
                        :class="{ 'lg:hidden': collapsed && !mobileOpen }" title="Sign Out">
                        <Icons name="LogOut" class="w-4 h-4" />
                    </button>
                </transition>
            </div>
        </aside>

        <!-- Main Content -->
        <div class="flex-1 flex flex-col min-h-screen transition-[margin-left] duration-250 ease-in-out ml-0"
            :class="collapsed ? 'lg:ml-18' : 'lg:ml-60'">
            <!-- Top header -->
            <header class="h-18 bg-surface border-b border-border-light sticky top-0 z-10 px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-3"
                :class="{'lg:h-20': collapsed, 'md:h-20': !collapsed} "
            >
                <!-- Hamburger (mobile) -->
                <button @click="toggleMobile" class="lg:hidden p-1.5 -ml-1 rounded-lg hover:bg-page text-ink-secondary">
                    <Icons name="Menu" class="w-5 h-5" />
                </button>
                <div class="flex-1 min-w-0">
                    <h2 class="text-base font-semibold text-ink truncate">{{ route.meta.title || 'Overview' }}</h2>
                </div>
                <div class="flex items-center gap-3">
                    <NotificationBell />
                    <div class="text-sm text-ink-muted hidden sm:block whitespace-nowrap">
                        {{ new Date().toLocaleDateString('en-US', {weekday: 'long', year: 'numeric', month: 'long', day:'numeric'}) }}
                    </div>
                </div>
            </header>
            <main class="px-4 sm:px-6 lg:px-8 py-5 lg:py-7 flex-1">
                <router-view v-slot="{ Component }">
                    <transition name="page" mode="out-in">
                        <component :is="Component" />
                    </transition>
                </router-view>
            </main>
        </div>
    </div>
</template>

<style scoped>
.fade-text-enter-active {
    transition: opacity 0.2s ease 0.1s;
}

.fade-text-leave-active {
    transition: opacity 0.1s ease;
}

.fade-text-enter-from,
.fade-text-leave-to {
    opacity: 0;
}

.fade-overlay-enter-active {
    transition: opacity 0.2s ease;
}

.fade-overlay-leave-active {
    transition: opacity 0.15s ease;
}

.fade-overlay-enter-from,
.fade-overlay-leave-to {
    opacity: 0;
}

.page-enter-active,
.page-leave-active {
    transition: all 0.2s ease-out;
}

.page-enter-from {
    opacity: 0;
    transform: translateY(6px);
}

.page-leave-to {
    opacity: 0;
    transform: translateY(-6px);
}
</style>