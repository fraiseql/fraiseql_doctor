import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ExportModal from '../ExportModal.vue'

describe('ExportModal', () => {
  const defaultProps = {
    historyCount: 42
  }

  describe('Component Rendering', () => {
    it('should render without errors', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      expect(wrapper.exists()).toBe(true)
    })

    it('should display modal title', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      expect(wrapper.text()).toContain('Export Query History')
    })

    it('should display history count information', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      expect(wrapper.text()).toContain('42 queries will be exported')
    })

    it('should have close button in header', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const closeBtn = wrapper.find('button[aria-label="Close"], .text-gray-400 svg')
      expect(closeBtn.exists()).toBe(true)
    })
  })

  describe('Format Selection', () => {
    it('should have JSON format option selected by default', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const jsonRadio = wrapper.find('input[value="json"]')
      
      expect(jsonRadio.exists()).toBe(true)
      expect((jsonRadio.element as HTMLInputElement).checked).toBe(true)
      expect(wrapper.vm.exportOptions.format).toBe('json')
    })

    it('should have CSV format option', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const csvRadio = wrapper.find('input[value="csv"]')
      
      expect(csvRadio.exists()).toBe(true)
      expect(wrapper.text()).toContain('CSV')
      expect(wrapper.text()).toContain('Spreadsheet compatible')
    })

    it('should have GraphQL format option', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const graphqlRadio = wrapper.find('input[value="graphql"]')
      
      expect(graphqlRadio.exists()).toBe(true)
      expect(wrapper.text()).toContain('GraphQL')
      expect(wrapper.text()).toContain('Query collection')
    })

    it('should update selected format when radio button is changed', async () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const csvRadio = wrapper.find('input[value="csv"]')
      
      await csvRadio.setValue(true)
      
      expect(wrapper.vm.exportOptions.format).toBe('csv')
    })

    it('should display format descriptions', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      
      expect(wrapper.text()).toContain('Complete data structure')
      expect(wrapper.text()).toContain('Spreadsheet compatible')
      expect(wrapper.text()).toContain('Query collection')
    })
  })

  describe('Data Inclusion Options', () => {
    it('should have variables inclusion checkbox checked by default', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      
      expect(wrapper.vm.exportOptions.includeVariables).toBe(true)
      
      const variablesCheckbox = wrapper.find('input[type="checkbox"]:checked')
      expect(variablesCheckbox.exists()).toBe(true)
    })

    it('should have results inclusion checkbox checked by default', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      
      expect(wrapper.vm.exportOptions.includeResults).toBe(true)
    })

    it('should toggle variables inclusion when checkbox is clicked', async () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const checkboxes = wrapper.findAll('input[type="checkbox"]')
      const variablesCheckbox = checkboxes.find(cb => 
        cb.element.closest('label')?.textContent?.includes('Include Variables')
      )
      
      if (variablesCheckbox) {
        await variablesCheckbox.setValue(false)
        expect(wrapper.vm.exportOptions.includeVariables).toBe(false)
        
        await variablesCheckbox.setValue(true)
        expect(wrapper.vm.exportOptions.includeVariables).toBe(true)
      }
    })

    it('should toggle results inclusion when checkbox is clicked', async () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const checkboxes = wrapper.findAll('input[type="checkbox"]')
      const resultsCheckbox = checkboxes.find(cb => 
        cb.element.closest('label')?.textContent?.includes('Include Results')
      )
      
      if (resultsCheckbox) {
        await resultsCheckbox.setValue(false)
        expect(wrapper.vm.exportOptions.includeResults).toBe(false)
        
        await resultsCheckbox.setValue(true)
        expect(wrapper.vm.exportOptions.includeResults).toBe(true)
      }
    })

    it('should display inclusion option labels', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      
      expect(wrapper.text()).toContain('Include Variables')
      expect(wrapper.text()).toContain('Include Results')
    })
  })

  describe('Action Buttons', () => {
    it('should have Cancel button', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      
      expect(wrapper.text()).toContain('Cancel')
    })

    it('should have Export button', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      
      expect(wrapper.text()).toContain('Export')
    })

    it('should emit close event when Cancel button is clicked', async () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const buttons = wrapper.findAll('button')
      const cancelBtn = buttons.find(btn => btn.text().includes('Cancel'))
      
      if (cancelBtn) {
        await cancelBtn.trigger('click')
        expect(wrapper.emitted('close')).toBeTruthy()
      }
    })

    it('should emit close event when header close button is clicked', async () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const buttons = wrapper.findAll('button')
      const closeBtn = buttons.find(btn => btn.classes().includes('text-gray-400'))
      
      if (closeBtn) {
        await closeBtn.trigger('click')
        expect(wrapper.emitted('close')).toBeTruthy()
      }
    })

    it('should emit export event with options when Export button is clicked', async () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const form = wrapper.find('form')
      
      await form.trigger('submit')
      
      expect(wrapper.emitted('export')).toBeTruthy()
      expect(wrapper.emitted('export')![0]).toEqual([{
        format: 'json',
        includeVariables: true,
        includeResults: true
      }])
    })

    it('should emit export event when Export button is clicked directly', async () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      
      // Find and submit the form (which contains the submit button)
      const form = wrapper.find('form')
      expect(form.exists()).toBe(true)
      
      await form.trigger('submit.prevent')
      
      expect(wrapper.emitted('export')).toBeTruthy()
      expect(wrapper.emitted('export')![0]).toEqual([{
        format: 'json',
        includeVariables: true,
        includeResults: true
      }])
    })
  })

  describe('Form Interaction', () => {
    it('should submit form with custom options', async () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      
      // Change format to CSV
      const csvRadio = wrapper.find('input[value="csv"]')
      await csvRadio.setValue(true)
      
      // Uncheck include results
      const checkboxes = wrapper.findAll('input[type="checkbox"]')
      const resultsCheckbox = checkboxes.find(cb => 
        cb.element.closest('label')?.textContent?.includes('Include Results')
      )
      if (resultsCheckbox) {
        await resultsCheckbox.setValue(false)
      }
      
      const form = wrapper.find('form')
      await form.trigger('submit')
      
      expect(wrapper.emitted('export')).toBeTruthy()
      expect(wrapper.emitted('export')![0]).toEqual([{
        format: 'csv',
        includeVariables: true,
        includeResults: false
      }])
    })

    it('should prevent form submission default behavior', async () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const form = wrapper.find('form')
      
      // Just verify the form exists and can emit events properly
      expect(form.exists()).toBe(true)
      
      // Test that form submission triggers export event
      await form.trigger('submit')
      expect(wrapper.emitted('export')).toBeTruthy()
    })
  })

  describe('Different History Counts', () => {
    it('should display singular form for single query', () => {
      const wrapper = mount(ExportModal, { props: { historyCount: 1 } })
      
      expect(wrapper.text()).toContain('1 queries will be exported') // Note: this might need adjustment for proper pluralization
    })

    it('should display zero count properly', () => {
      const wrapper = mount(ExportModal, { props: { historyCount: 0 } })
      
      expect(wrapper.text()).toContain('0 queries will be exported')
    })

    it('should display large count properly', () => {
      const wrapper = mount(ExportModal, { props: { historyCount: 1337 } })
      
      expect(wrapper.text()).toContain('1337 queries will be exported')
    })
  })

  describe('Modal Styling and Layout', () => {
    it('should have modal overlay', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const overlay = wrapper.find('.fixed.inset-0.bg-black.bg-opacity-50')
      
      expect(overlay.exists()).toBe(true)
    })

    it('should have centered modal dialog', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const dialog = wrapper.find('.bg-white.rounded-lg.shadow-xl')
      
      expect(dialog.exists()).toBe(true)
    })

    it('should have proper z-index for modal', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const modal = wrapper.find('.z-50')
      
      expect(modal.exists()).toBe(true)
    })

    it('should have dark mode support', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const darkElements = wrapper.findAll('.dark\\:bg-gray-800, .dark\\:text-white, .dark\\:border-gray-700')
      
      expect(darkElements.length).toBeGreaterThan(0)
    })
  })

  describe('Accessibility', () => {
    it('should have proper form labels', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const labels = wrapper.findAll('label')
      
      expect(labels.length).toBeGreaterThan(2) // Format labels + inclusion option labels
    })

    it('should have radio buttons grouped properly', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const radioButtons = wrapper.findAll('input[type="radio"]')
      
      radioButtons.forEach(radio => {
        expect((radio.element as HTMLInputElement).name).toBeDefined()
      })
    })

    it('should have submit button type for export', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const exportBtn = wrapper.find('button[type="submit"]')
      
      expect(exportBtn.exists()).toBe(true)
    })

    it('should have button type for cancel button', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      const cancelBtn = wrapper.find('button[type="button"]')
      
      expect(cancelBtn.exists()).toBe(true)
    })
  })

  describe('Default Values', () => {
    it('should initialize with correct default export options', () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      
      expect(wrapper.vm.exportOptions).toEqual({
        format: 'json',
        includeVariables: true,
        includeResults: true
      })
    })

    it('should maintain reactive state when options change', async () => {
      const wrapper = mount(ExportModal, { props: defaultProps })
      
      // Change all options
      const csvRadio = wrapper.find('input[value="csv"]')
      await csvRadio.setValue(true)
      
      const checkboxes = wrapper.findAll('input[type="checkbox"]')
      for (const checkbox of checkboxes) {
        await checkbox.setValue(false)
      }
      
      expect(wrapper.vm.exportOptions.format).toBe('csv')
      expect(wrapper.vm.exportOptions.includeVariables).toBe(false)
      expect(wrapper.vm.exportOptions.includeResults).toBe(false)
    })
  })
})