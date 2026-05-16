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

