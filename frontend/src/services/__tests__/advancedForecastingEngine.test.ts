import { describe, it, expect, beforeEach, vi } from 'vitest'
import { AdvancedForecastingEngine } from '../advancedForecastingEngine'
import type { QueryMetric } from '../performanceMonitor'

describe('AdvancedForecastingEngine', () => {
  let forecastingEngine: AdvancedForecastingEngine

  const createMockMetric = (overrides: Partial<QueryMetric> = {}): QueryMetric => ({
    query: 'test query',
    variables: {},
    executionTime: 100,
    responseSize: 1024,
    timestamp: new Date(),
    status: 'success',
    endpointId: 'endpoint-1',
    operationType: 'query',
    ...overrides
  })

  beforeEach(() => {
    forecastingEngine = new AdvancedForecastingEngine({
      modelType: 'hybrid',
      seasonalityDetection: true,
      anomalyAwareForecasting: true
    })
  })

  describe('Time Series Modeling', () => {
    it('should detect and model seasonal patterns', async () => {
      // Generate synthetic seasonal data (daily + weekly patterns)
      const seasonalData = Array.from({ length: 24 * 14 }, (_, i) => { // 2 weeks hourly
        const hourOfDay = i % 24
        const dayOfWeek = Math.floor(i / 24) % 7

        const dailyPattern = Math.sin((hourOfDay / 24) * 2 * Math.PI) * 20
        const weeklyPattern = dayOfWeek < 5 ? 15 : -15 // Weekday vs weekend
        const baseValue = 100
        const noise = Math.random() * 10 - 5

        return createMockMetric({
          executionTime: baseValue + dailyPattern + weeklyPattern + noise,
          timestamp: new Date(Date.now() - (24 * 14 - i) * 60 * 60 * 1000)
        })
      })

      const seasonalAnalysis = await forecastingEngine.analyzeSeasonality(seasonalData)

      expect(seasonalAnalysis.patterns.daily.detected).toBe(true)
      expect(seasonalAnalysis.patterns.weekly.detected).toBe(true)
      expect(seasonalAnalysis.patterns.daily.strength).toBeGreaterThan(0.3)
      expect(seasonalAnalysis.patterns.weekly.strength).toBeGreaterThan(0.2)
      expect(seasonalAnalysis.decomposition.trend).toHaveLength(seasonalData.length)
      expect(seasonalAnalysis.decomposition.seasonal).toHaveLength(seasonalData.length)
      expect(seasonalAnalysis.decomposition.residual).toHaveLength(seasonalData.length)
    })

    it('should build ARIMA models for trend forecasting', async () => {
      const trendingData = Array.from({ length: 200 }, (_, i) =>
        createMockMetric({
          executionTime: 100 + i * 0.5 + Math.sin(i * 0.1) * 10 + Math.random() * 5,
          timestamp: new Date(Date.now() - (200 - i) * 60000)
        })
      )

      const arimaModel = await forecastingEngine.buildARIMAModel(trendingData, {
        autoOrder: true,
        maxP: 3,
        maxD: 2,
        maxQ: 3
      })

      expect(arimaModel.order.p).toBeGreaterThanOrEqual(0)
      expect(arimaModel.order.d).toBeGreaterThanOrEqual(0)
      expect(arimaModel.order.q).toBeGreaterThanOrEqual(0)
      expect(arimaModel.coefficients.length).toBeGreaterThan(0)
      expect(arimaModel.fitStatistics.aic).toBeGreaterThan(0)
      expect(arimaModel.fitStatistics.bic).toBeGreaterThan(0)
      expect(arimaModel.residuals.length).toBe(trendingData.length)
    })

    it('should implement exponential smoothing for short-term forecasts', async () => {
      const recentData = Array.from({ length: 48 }, (_, i) =>
        createMockMetric({
          executionTime: 100 + Math.random() * 20,
          timestamp: new Date(Date.now() - (48 - i) * 60 * 60 * 1000)
        })
      )

      const smoothingModel = await forecastingEngine.buildExponentialSmoothingModel(recentData, {
        method: 'holt_winters',
        alpha: null, // Auto-optimize
        beta: null,
        gamma: null,
        seasonal: 'additive'
      })

      expect(smoothingModel.parameters.alpha).toBeGreaterThan(0)
      expect(smoothingModel.parameters.alpha).toBeLessThan(1)
      expect(smoothingModel.parameters.beta).toBeGreaterThan(0)
      expect(smoothingModel.parameters.beta).toBeLessThan(1)
      expect(smoothingModel.parameters.gamma).toBeGreaterThan(0)
      expect(smoothingModel.parameters.gamma).toBeLessThan(1)
      expect(smoothingModel.forecastFunction).toBeTypeOf('function')
      expect(smoothingModel.fittedValues.length).toBe(recentData.length)
    })
  })

  describe('Multi-step Forecasting', () => {
    it('should generate probabilistic forecasts with confidence intervals', async () => {
      const historicalData = Array.from({ length: 168 }, (_, i) => // 1 week hourly
        createMockMetric({
          executionTime: 100 + Math.sin(i * 0.1) * 15 + Math.random() * 10,
          timestamp: new Date(Date.now() - (168 - i) * 60 * 60 * 1000)
        })
      )

      const forecast = await forecastingEngine.generateProbabilisticForecast(historicalData, {
        horizonHours: 24,
        confidenceLevels: [0.5, 0.8, 0.95],
        includeSeasonality: true,
        method: 'ensemble'
      })

      expect(forecast.predictions).toHaveLength(24)

      for (const prediction of forecast.predictions) {
        expect(prediction.pointForecast).toBeGreaterThan(0)
        expect(prediction.intervals.length).toBe(3) // 50%, 80%, 95%
        expect(prediction.intervals[0].lower).toBeLessThan(prediction.pointForecast)
        expect(prediction.intervals[0].upper).toBeGreaterThan(prediction.pointForecast)
        expect(prediction.intervals[2].upper - prediction.intervals[2].lower)
          .toBeGreaterThan(prediction.intervals[0].upper - prediction.intervals[0].lower)
      }
    })

    it('should handle forecast uncertainty quantification', async () => {
      const noisyData = Array.from({ length: 100 }, (_, i) =>
        createMockMetric({
          executionTime: 100 + Math.random() * 50, // High variability
          timestamp: new Date(Date.now() - (100 - i) * 60000)
        })
      )

      const uncertaintyAnalysis = await forecastingEngine.quantifyUncertainty(noisyData, {
        method: 'bootstrap',
        bootstrapSamples: 1000,
        forecastHorizon: 12
      })

      expect(uncertaintyAnalysis.aleatoric.value).toBeGreaterThan(0) // Data uncertainty
      expect(uncertaintyAnalysis.epistemic.value).toBeGreaterThan(0) // Model uncertainty
      expect(uncertaintyAnalysis.total.value).toBeGreaterThan(
        Math.max(uncertaintyAnalysis.aleatoric.value, uncertaintyAnalysis.epistemic.value)
      )
      expect(uncertaintyAnalysis.confidenceDegradation.length).toBe(12)
    })

    it('should implement ensemble forecasting for improved accuracy', async () => {
      const trainData = Array.from({ length: 200 }, (_, i) =>
        createMockMetric({
          executionTime: 100 + i * 0.3 + Math.sin(i * 0.15) * 12 + Math.random() * 8,
          timestamp: new Date(Date.now() - (200 - i) * 60000)
        })
      )

      const ensembleForecast = await forecastingEngine.generateEnsembleForecast(trainData, {
        models: ['arima', 'exponential_smoothing', 'linear_regression', 'lstm'],
        weights: 'adaptive', // Adaptive weighting based on recent performance
        forecastHorizon: 24
      })

      expect(ensembleForecast.models.length).toBe(4)
      expect(ensembleForecast.weights.reduce((sum, w) => sum + w, 0)).toBeCloseTo(1, 2)
      expect(ensembleForecast.combinedPredictions).toHaveLength(24)
      expect(ensembleForecast.individualPredictions.arima).toHaveLength(24)
      expect(ensembleForecast.performanceMetrics.ensembleScore).toBeGreaterThan(0)
    })
  })

  describe('Anomaly-Aware Forecasting', () => {
    it('should exclude anomalies from model training data', async () => {
      const dataWithAnomalies = Array.from({ length: 100 }, (_, i) =>
        createMockMetric({
          executionTime: i === 50 ? 500 : (100 + Math.random() * 20), // Single spike anomaly
          timestamp: new Date(Date.now() - (100 - i) * 60000)
        })
      )

      const robustForecast = await forecastingEngine.generateRobustForecast(dataWithAnomalies, {
        anomalyDetection: true,
        outlierThreshold: 3,
        cleaningMethod: 'isolation_forest'
      })

      expect(robustForecast.cleanedData.length).toBeLessThan(dataWithAnomalies.length)
      expect(robustForecast.detectedAnomalies).toHaveLength(1)
      expect(robustForecast.detectedAnomalies[0].index).toBe(50)
      expect(robustForecast.modelQuality.cleanlinessScore).toBeGreaterThan(0.9)
    })

    it('should predict future anomaly probabilities', async () => {
      const historicalWithPatterns = Array.from({ length: 168 }, (_, i) => {
        const hourOfDay = i % 24
        const isAnomaly = hourOfDay === 3 && Math.random() < 0.3 // 30% chance at 3 AM

        return createMockMetric({
          executionTime: isAnomaly ? 300 : (100 + Math.random() * 20),
          timestamp: new Date(Date.now() - (168 - i) * 60 * 60 * 1000)
        })
      })

      const anomalyForecast = await forecastingEngine.forecastAnomalyProbabilities(
        historicalWithPatterns,
        { horizon: 24, method: 'isolation_forest_temporal' }
      )

      expect(anomalyForecast.hourlyProbabilities).toHaveLength(24)
      expect(anomalyForecast.hourlyProbabilities[3]).toBeGreaterThan(0.1) // High prob at 3 AM (peak hour)
      expect(anomalyForecast.hourlyProbabilities[12]).toBeGreaterThan(0.1) // Business hour has baseline anomaly risk
      expect(anomalyForecast.expectedAnomalies).toBeGreaterThan(0)
    })

    it('should adjust forecast confidence based on anomaly likelihood', async () => {
      const stabilityData = Array.from({ length: 100 }, (_, i) =>
        createMockMetric({
          executionTime: 100 + Math.random() * 10, // Very stable
          timestamp: new Date(Date.now() - (100 - i) * 60000)
        })
      )

      const adaptiveForecast = await forecastingEngine.generateAdaptiveConfidenceForecast(
        stabilityData,
        { horizon: 12, anomalyAwareness: true }
      )

      for (let i = 0; i < adaptiveForecast.predictions.length; i++) {
        const prediction = adaptiveForecast.predictions[i]
        expect(prediction.adaptiveConfidence).toBeDefined()
        expect(prediction.anomalyRisk).toBeGreaterThanOrEqual(0)
        expect(prediction.anomalyRisk).toBeLessThanOrEqual(1)

        // Confidence should decrease with forecast horizon
        if (i > 0) {
          expect(prediction.adaptiveConfidence).toBeLessThanOrEqual(
            adaptiveForecast.predictions[i - 1].adaptiveConfidence + 0.1
          )
        }
      }
    })
  })

  describe('Model Validation and Selection', () => {
    it('should perform walk-forward validation for model assessment', async () => {
      const validationData = Array.from({ length: 200 }, (_, i) =>
        createMockMetric({
          executionTime: 100 + i * 0.2 + Math.sin(i * 0.1) * 15 + Math.random() * 8,
          timestamp: new Date(Date.now() - (200 - i) * 60000)
        })
      )

      const validation = await forecastingEngine.performWalkForwardValidation(validationData, {
        initialTrainingSize: 100,
        forecastHorizon: 12,
        stepSize: 6,
        models: ['arima', 'exponential_smoothing']
      })

      expect(validation.results.length).toBeGreaterThan(5) // Multiple validation windows
      expect(validation.aggregatedMetrics.mae.arima).toBeGreaterThan(0)
      expect(validation.aggregatedMetrics.mae.exponential_smoothing).toBeGreaterThan(0)
      expect(validation.bestModel).toMatch(/arima|exponential_smoothing/)
      expect(validation.stabilityMetrics.maeVariance).toBeGreaterThan(0)
    })

    it('should implement automated model selection with hyperparameter tuning', async () => {
      const tuningData = Array.from({ length: 150 }, (_, i) =>
        createMockMetric({
          executionTime: 100 + Math.sin(i * 0.08) * 20 + Math.random() * 5,
          timestamp: new Date(Date.now() - (150 - i) * 60000)
        })
      )

      const autoSelection = await forecastingEngine.autoSelectModel(tuningData, {
        candidateModels: ['arima', 'exponential_smoothing', 'prophet'],
        validationSplit: 0.3,
        hyperparameterTuning: true,
        optimizationMetric: 'mae'
      })

      expect(autoSelection.selectedModel.type).toMatch(/arima|exponential_smoothing|prophet/)
      expect(autoSelection.selectedModel.hyperparameters).toBeDefined()
      expect(autoSelection.crossValidationScore).toBeGreaterThan(0)
      expect(autoSelection.allModelResults.length).toBe(3)
      expect(autoSelection.selectionReason).toContain('lowest')
    })

    it('should calculate comprehensive forecast accuracy metrics', async () => {
      const actualValues = Array.from({ length: 24 }, (_, i) =>
        100 + Math.sin(i * 0.1) * 10 + Math.random() * 5
      )

      const forecastValues = actualValues.map(v => v + (Math.random() - 0.5) * 10)

      const accuracyMetrics = await forecastingEngine.calculateForecastAccuracy(
        actualValues,
        forecastValues,
        { includeDirectional: true, includeDistribution: true }
      )

      expect(accuracyMetrics.mae).toBeGreaterThan(0) // Mean Absolute Error
      expect(accuracyMetrics.rmse).toBeGreaterThan(0) // Root Mean Square Error
      expect(accuracyMetrics.mape).toBeGreaterThan(0) // Mean Absolute Percentage Error
      expect(accuracyMetrics.smape).toBeGreaterThanOrEqual(0) // Symmetric MAPE
      expect(accuracyMetrics.smape).toBeLessThanOrEqual(200)
      expect(accuracyMetrics.directionalAccuracy).toBeGreaterThanOrEqual(0)
      expect(accuracyMetrics.directionalAccuracy).toBeLessThanOrEqual(1)
      expect(accuracyMetrics.distributionalMetrics.ks_statistic).toBeDefined()
    })
  })

  describe('Real-time Model Updates', () => {
    it('should support online learning for model adaptation', async () => {
      const initialData = Array.from({ length: 100 }, (_, i) =>
        createMockMetric({
          executionTime: 100 + Math.random() * 20,
          timestamp: new Date(Date.now() - (100 - i) * 60000)
        })
      )

      const onlineModel = await forecastingEngine.initializeOnlineModel(initialData, {
        modelType: 'adaptive_arima',
        adaptationRate: 0.1,
        forgettingFactor: 0.95
      })

      expect(onlineModel.modelState).toBeDefined()
      expect(onlineModel.adaptationConfig.learningRate).toBe(0.1)

      // Simulate new data points
      for (let i = 0; i < 10; i++) {
        const newPoint = createMockMetric({
          executionTime: 120 + Math.random() * 15, // Slight shift in pattern
          timestamp: new Date(Date.now() + i * 60000)
        })

        await forecastingEngine.updateOnlineModel(onlineModel, newPoint)
      }

      expect(onlineModel.updateCount).toBe(10)
      expect(onlineModel.adaptationHistory.length).toBe(10)
    })

    it('should detect concept drift and trigger model retraining', async () => {
      const stableData = Array.from({ length: 100 }, () =>
        createMockMetric({ executionTime: 100 + Math.random() * 10 })
      )

      const driftData = Array.from({ length: 50 }, () =>
        createMockMetric({ executionTime: 150 + Math.random() * 10 }) // Distribution shift
      )

      const driftDetection = await forecastingEngine.detectConceptDrift(
        stableData,
        driftData,
        { method: 'page_hinkley', sensitivity: 0.05 }
      )

      expect(driftDetection.driftDetected).toBe(true)
      expect(driftDetection.driftPoint).toBeGreaterThan(0)
      expect(driftDetection.driftMagnitude).toBeGreaterThan(0.5)
      expect(driftDetection.confidence).toBeGreaterThan(0.8)
      expect(driftDetection.recommendedAction).toBe('retrain_model')
    })

    it('should maintain model versioning and rollback capabilities', async () => {
      const trainingData = Array.from({ length: 100 }, (_, i) =>
        createMockMetric({
          executionTime: 100 + i * 0.1 + Math.random() * 5,
          timestamp: new Date(Date.now() - (100 - i) * 60000)
        })
      )

      // Train initial model
      const model_v1 = await forecastingEngine.trainModel(trainingData, { version: 'v1.0' })
      expect(model_v1.metadata.version).toBe('v1.0')

      // Train updated model
      const model_v2 = await forecastingEngine.trainModel(trainingData, { version: 'v2.0' })
      expect(model_v2.metadata.version).toBe('v2.0')

      // Rollback capability
      const rolledBackModel = await forecastingEngine.rollbackToVersion('v1.0')
      expect(rolledBackModel.metadata.version).toBe('v1.0')
      expect(rolledBackModel.modelId).toBe(model_v1.modelId)

      // Version history
      const versionHistory = await forecastingEngine.getModelVersionHistory()
      expect(versionHistory.length).toBeGreaterThanOrEqual(2)
      expect(versionHistory.map(v => v.version)).toContain('v1.0')
      expect(versionHistory.map(v => v.version)).toContain('v2.0')
    })
  })
})
