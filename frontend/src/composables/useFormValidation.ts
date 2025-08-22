import { ref, computed } from 'vue'

export interface ValidationRule {
  required?: boolean
  minLength?: number
  maxLength?: number
  pattern?: RegExp
  custom?: (value: any) => string | null
}

export interface ValidationRules {
  [key: string]: ValidationRule
}

export function useFormValidation<T extends Record<string, any>>(
  data: T,
  rules: ValidationRules
) {
  const errors = ref<Record<keyof T, string>>({} as Record<keyof T, string>)

  const validateField = (field: keyof T, value: any): string => {
    const rule = rules[field as string]
    if (!rule) return ''

    if (rule.required && (!value || (typeof value === 'string' && value.trim() === ''))) {
      return `${String(field)} is required`
    }

    if (rule.minLength && typeof value === 'string' && value.length < rule.minLength) {
      return `${String(field)} must be at least ${rule.minLength} characters`
    }

    if (rule.maxLength && typeof value === 'string' && value.length > rule.maxLength) {
      return `${String(field)} must be no more than ${rule.maxLength} characters`
    }

    if (rule.pattern && typeof value === 'string' && !rule.pattern.test(value)) {
      return `${String(field)} format is invalid`
    }

    if (rule.custom) {
      const customError = rule.custom(value)
      if (customError) return customError
    }

    return ''
  }

  const validate = (): boolean => {
    let hasErrors = false

    for (const field in rules) {
      const error = validateField(field as keyof T, data[field as keyof T])
      errors.value[field as keyof T] = error
      if (error) hasErrors = true
    }

    return !hasErrors
  }

  const clearError = (field: keyof T) => {
    errors.value[field] = ''
  }

  const isValid = computed(() => {
    return Object.values(errors.value).every(error => !error)
  })

  return {
    errors,
    validate,
    validateField,
    clearError,
    isValid
  }
}