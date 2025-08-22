import { ref, computed, watch } from 'vue'
import type { Ref } from 'vue'

export interface TimeRange {
  start: Date
  end: Date
}

export interface ZoomState {
  start: number
  end: number
}

export interface ChartSynchronizationState {
  globalTimeRange: Ref<TimeRange | null>
  globalZoomState: Ref<ZoomState>
  synchronizedCharts: Ref<Set<string>>
  isGlobalSync: Ref<boolean>
}

const globalState: ChartSynchronizationState = {
  globalTimeRange: ref(null),
  globalZoomState: ref({ start: 0, end: 100 }),
  synchronizedCharts: ref(new Set()),
  isGlobalSync: ref(false)
}

export function useChartSynchronization() {
  // Register a chart for synchronization
  const registerChart = (chartId: string) => {
    globalState.synchronizedCharts.value.add(chartId)
  }

  // Unregister a chart from synchronization
  const unregisterChart = (chartId: string) => {
    globalState.synchronizedCharts.value.delete(chartId)
  }

  // Enable/disable global synchronization
  const setGlobalSync = (enabled: boolean) => {
    globalState.isGlobalSync.value = enabled
  }

  // Update global time range
  const setGlobalTimeRange = (timeRange: TimeRange | null) => {
    globalState.globalTimeRange.value = timeRange
  }

  // Update global zoom state
  const setGlobalZoomState = (zoomState: ZoomState) => {
    if (globalState.isGlobalSync.value) {
      globalState.globalZoomState.value = zoomState
    }
  }

  // Handle zoom event from a specific chart
  const handleChartZoom = (chartId: string, zoomState: ZoomState) => {
    if (globalState.isGlobalSync.value && globalState.synchronizedCharts.value.has(chartId)) {
      setGlobalZoomState(zoomState)
    }
  }

  // Calculate time range from zoom state and data
  const calculateTimeRangeFromZoom = (
    zoomState: ZoomState,
    dataTimeRange: { min: Date; max: Date }
  ): TimeRange => {
    const totalDuration = dataTimeRange.max.getTime() - dataTimeRange.min.getTime()
    const startOffset = (zoomState.start / 100) * totalDuration
    const endOffset = (zoomState.end / 100) * totalDuration

    return {
      start: new Date(dataTimeRange.min.getTime() + startOffset),
      end: new Date(dataTimeRange.min.getTime() + endOffset)
    }
  }

  // Get data time range from metrics
  const getDataTimeRange = (metrics: Array<{ timestamp: Date | string }>) => {
    if (!metrics.length) {
      const now = new Date()
      return { min: now, max: now }
    }

    const timestamps = metrics.map(m =>
      typeof m.timestamp === 'string' ? new Date(m.timestamp) : m.timestamp
    )

    return {
      min: new Date(Math.min(...timestamps.map(t => t.getTime()))),
      max: new Date(Math.max(...timestamps.map(t => t.getTime())))
    }
  }

  // Reset synchronization state
  const resetSynchronization = () => {
    globalState.globalTimeRange.value = null
    globalState.globalZoomState.value = { start: 0, end: 100 }
    globalState.isGlobalSync.value = false
  }

  // Computed properties for reactivity
  const synchronizedChartsCount = computed(() => globalState.synchronizedCharts.value.size)

  const isSynchronizationActive = computed(() =>
    globalState.isGlobalSync.value && synchronizedChartsCount.value > 1
  )

  // Watch for changes in global zoom state to propagate to charts
  const onGlobalZoomChange = (callback: (zoomState: ZoomState) => void) => {
    return watch(
      () => globalState.globalZoomState.value,
      (newZoomState) => {
        if (globalState.isGlobalSync.value) {
          callback(newZoomState)
        }
      },
      { deep: true }
    )
  }

  // Watch for changes in global time range
  const onGlobalTimeRangeChange = (callback: (timeRange: TimeRange | null) => void) => {
    return watch(
      () => globalState.globalTimeRange.value,
      (newTimeRange) => {
        callback(newTimeRange)
      },
      { deep: true }
    )
  }

  return {
    // State
    globalTimeRange: globalState.globalTimeRange,
    globalZoomState: globalState.globalZoomState,
    synchronizedCharts: globalState.synchronizedCharts,
    isGlobalSync: globalState.isGlobalSync,

    // Computed
    synchronizedChartsCount,
    isSynchronizationActive,

    // Methods
    registerChart,
    unregisterChart,
    setGlobalSync,
    setGlobalTimeRange,
    setGlobalZoomState,
    handleChartZoom,
    calculateTimeRangeFromZoom,
    getDataTimeRange,
    resetSynchronization,

    // Event watchers
    onGlobalZoomChange,
    onGlobalTimeRangeChange
  }
}

// Additional utility for chart overlay management
export interface ChartOverlays {
  movingAverage: { enabled: boolean; window: number }
  percentileBands: { enabled: boolean; percentiles: number[] }
  anomalyHighlights: { enabled: boolean; threshold: number }
  trendLine: { enabled: boolean; method: string }
}

export function useChartOverlays() {
  const overlays = ref<ChartOverlays>({
    movingAverage: { enabled: false, window: 5 },
    percentileBands: { enabled: false, percentiles: [25, 75, 95] },
    anomalyHighlights: { enabled: false, threshold: 2 },
    trendLine: { enabled: false, method: 'linear' }
  })

  const toggleOverlay = (
    overlayType: keyof ChartOverlays,
    enabled: boolean,
    config?: Partial<ChartOverlays[keyof ChartOverlays]>
  ) => {
    overlays.value[overlayType] = {
      ...overlays.value[overlayType],
      enabled,
      ...config
    } as any
  }

  const resetOverlays = () => {
    overlays.value = {
      movingAverage: { enabled: false, window: 5 },
      percentileBands: { enabled: false, percentiles: [25, 75, 95] },
      anomalyHighlights: { enabled: false, threshold: 2 },
      trendLine: { enabled: false, method: 'linear' }
    }
  }

  const getOverlayConfig = (overlayType: keyof ChartOverlays) => {
    return overlays.value[overlayType]
  }

  return {
    overlays,
    toggleOverlay,
    resetOverlays,
    getOverlayConfig
  }
}
