<script setup>
import { computed } from 'vue'
import * as LucideIcons from 'lucide-vue-next'

const props = defineProps({
    name: String,
    size: { type: String, default: 'w-5 h-5' }
})

const isMdi = computed(() => {
    const n = props.name || ''
    return n.startsWith('mdi-') || n.startsWith('mdi ')
})

const LucideIcon = computed(() => {
    if (isMdi.value) return null
    return LucideIcons[props.name] || LucideIcons.HelpCircle
})
</script>

<template>
    <i v-if="isMdi"
        :class="['mdi', props.name.startsWith('mdi-') ? props.name : '', size, 'inline-flex items-center justify-center translate-y-[2px]']"></i>
    <component v-else :is="LucideIcon" :class="size" />
</template>