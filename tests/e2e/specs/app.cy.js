/// <reference types="cypress" />

describe('School Management System E2E', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  describe('Dashboard', () => {
    it('should display the dashboard page', () => {
      cy.contains('Dashboard').should('be.visible')
      cy.contains('School Management System').should('be.visible')
    })

    it('should show API status card', () => {
      cy.contains('API Status').should('be.visible')
    })

    it('should show database status card', () => {
      cy.contains('Database').should('be.visible')
      cy.contains('PostgreSQL 18').should('be.visible')
    })

    it('should have navigation links', () => {
      cy.contains('Departments').should('be.visible')
      cy.contains('Courses').should('be.visible')
      cy.contains('Users').should('be.visible')
    })
  })

  describe('Navigation', () => {
    it('should navigate to Departments page', () => {
      cy.contains('a', 'Departments').click()
      cy.url().should('include', '/departments')
      cy.contains('h1', 'Departments').should('be.visible')
    })

    it('should navigate to Courses page', () => {
      cy.contains('a', 'Courses').click()
      cy.url().should('include', '/courses')
      cy.contains('h1', 'Courses').should('be.visible')
    })

    it('should navigate to Users page', () => {
      cy.contains('a', 'Users').click()
      cy.url().should('include', '/users')
      cy.contains('h1', 'Users').should('be.visible')
    })
  })

  describe('Departments Page', () => {
    beforeEach(() => {
      cy.visit('/departments')
    })

    it('should show create department button', () => {
      cy.contains('+ New Department').should('be.visible')
    })

    it('should toggle create form', () => {
      cy.contains('+ New Department').click()
      cy.contains('Create Department').should('be.visible')
      cy.contains('Cancel').click()
      cy.contains('Create Department').should('not.exist')
    })
  })

  describe('Courses Page', () => {
    beforeEach(() => {
      cy.visit('/courses')
    })

    it('should show create course button', () => {
      cy.contains('+ New Course').should('be.visible')
    })

    it('should toggle create form', () => {
      cy.contains('+ New Course').click()
      cy.contains('Create Course').should('be.visible')
      cy.contains('Cancel').click()
      cy.contains('Create Course').should('not.exist')
    })
  })
})
