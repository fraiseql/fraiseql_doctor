import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface DashboardStat {
  label: string
  value: number
  status: 'success' | 'warning' | 'error' | 'info'
}

export interface ChartData {
  labels: string[]
  datasets: Array<{
    label: string
    data: number[]
    borderColor: string
    backgroundColor: string
  }>
}

export interface DashboardData {
  stats: DashboardStat[]
  chartData: ChartData | null
}

export const useDashboard = defineStore('dashboard', () => {
  // State
  const stats = ref<DashboardStat[]>([])
  const chartData = ref<ChartData | null>(null)
  const isLoading = ref(true)
  const error = ref<string | null>(null)

  // Getters
  const hasData = computed(() => stats.value.length > 0)
  const isEmpty = computed(() => stats.value.length === 0 && !isLoading.value)

  // Actions
  const updateDashboardData = (data: DashboardData) => {
    stats.value = data.stats
    chartData.value = data.chartData
    isLoading.value = false
    error.value = null
  }

  const setLoading = (loading: boolean) => {
    isLoading.value = loading
  }

  const setError = (errorMessage: string) => {
    error.value = errorMessage
    isLoading.value = false
  }

  const reset = () => {
    stats.value = []
    chartData.value = null
    isLoading.value = true
    error.value = null
  }

  return {
    // State
    stats,
    chartData,
    isLoading,
    error,
    
    // Getters
    hasData,
    isEmpty,
    
    // Actions
    updateDashboardData,
    setLoading,
    setError,
    reset
  }
})