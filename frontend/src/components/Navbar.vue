<script setup>
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

const logout = async () => {
    await authStore.logout();
    router.push('/login');
};
</script>

<template>
    <nav class="bg-gray-800 p-4">
        <div class="container mx-auto flex justify-between items-center">
            <div class="text-white font-bold text-xl">School Management</div>
            <div class="flex space-x-4">
                <router-link to="/" class="text-gray-300 hover:text-white">Home</router-link>
                <router-link to="/students" class="text-gray-300 hover:text-white">Students</router-link>
                <router-link to="/teachers" class="text-gray-300 hover:text-white">Teachers</router-link>
                <router-link to="/courses" class="text-gray-300 hover:text-white">Courses</router-link>
                <router-link to="/classes" class="text-gray-300 hover:text-white">Classes</router-link>
                <router-link to="/enrollments" class="text-gray-300 hover:text-white">Enrollments</router-link>
                <router-link to="/logout" class="text-gray-300 hover:text-white" @click="logout">Logout</router-link>
            </div>
        </div>
    </nav>
</template>