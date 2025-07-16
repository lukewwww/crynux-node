import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSystemStore = defineStore('system', () => {

    const showWaveBg = ref(true)
    const showMinimizedNotification = ref(true)
    const showSettingsModal = ref(false)

    function setShowWaveBg(val) {
        showWaveBg.value = val
    }

    function setShowMinimizedNotification(val) {
        showMinimizedNotification.value = val
    }

    return {
        showWaveBg,
        setShowWaveBg,
        showMinimizedNotification,
        setShowMinimizedNotification,
        showSettingsModal
    }
})
