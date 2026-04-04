<script setup>
import { RouterView } from 'vue-router'
import ToastContainer from './components/ToastContainer.vue'

</script>

<template>
  <div class="min-h-screen font-sans antialiased">
    <RouterView />
    <ToastContainer />
  </div>
</template>

<style scoped>
    .fade-enter-active, .fade-leave-active {
    transition: opacity 0.3s ease;
    }
    .fade-enter-from, .fade-leave-to {
        opacity: 0;
    }
</style>