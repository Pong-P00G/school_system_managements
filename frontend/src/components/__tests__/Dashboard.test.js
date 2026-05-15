/**
 * Integration tests for Dashboard component using Vue Test Utils.
 *
 * To run: npm install --save-dev @vue/test-utils vitest jsdom
 * Then: npx vitest run
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Dashboard from '../../pages/Dashboard.vue'

// Mock the API module
vi.mock('../../api.js', () => ({
  getHealth: vi.fn(() =>
    Promise.resolve({
      data: { status: 'healthy', app: 'School Management System API', version: '1.0.0' },
    })
  ),
  getHealthDb: vi.fn(() =>
    Promise.resolve({
      data: { status: 'healthy', database: 'connected', app: 'School Management System API', version: '1.0.0' },
    })
  ),
}))

describe('Dashboard', () => {
  it('renders the dashboard heading', () => {
    const wrapper = mount(Dashboard)
    expect(wrapper.find('h1').text()).toBe('Dashboard')
  })

  it('shows loading state initially', () => {
    const wrapper = mount(Dashboard)
    expect(wrapper.text()).toContain('Loading system status...')
  })

  it('displays API status after loading', async () => {
    const wrapper = mount(Dashboard)
    await flushPromises()
    expect(wrapper.text()).toContain('healthy')
    expect(wrapper.text()).toContain('School Management System API')
  })

  it('displays database status after loading', async () => {
    const wrapper = mount(Dashboard)
    await flushPromises()
    expect(wrapper.text()).toContain('connected')
    expect(wrapper.text()).toContain('PostgreSQL 18')
  })

  it('shows welcome section', async () => {
    const wrapper = mount(Dashboard)
    await flushPromises()
    expect(wrapper.text()).toContain('Welcome to School Management System')
  })

  it('has navigation buttons', async () => {
    const wrapper = mount(Dashboard)
    await flushPromises()
    expect(wrapper.text()).toContain('View Departments')
    expect(wrapper.text()).toContain('View Courses')
  })
})
