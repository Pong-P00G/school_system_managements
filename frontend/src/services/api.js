import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to attach auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
    }
    return Promise.reject(error)
  }
)

export default api

// --- Health ---
export const getHealth = () => api.get('/health')
export const getHealthDb = () => api.get('/health/db')

// --- Auth ---
export const login = (username, password) =>
  api.post('/auth/login', { username, password })
export const register = (username, email, password) =>
  api.post('/auth/register', { username, email, password })

// --- Users ---
export const getUsers = (skip = 0, limit = 20, search = null, isActive = null) =>
  api.get('/users/', { params: { skip, limit, search, is_active: isActive } })
export const getUser = (userId) => api.get(`/users/${userId}`)
export const createUser = (data) => api.post('/users/', data)
export const updateUser = (userId, data) => api.put(`/users/${userId}`, data)
export const deleteUser = (userId) => api.delete(`/users/${userId}`)
export const assignRole = (userId, roleId) => api.post(`/users/${userId}/roles/${roleId}`)
export const removeRole = (userId, roleId) => api.delete(`/users/${userId}/roles/${roleId}`)
export const getRoles = () => api.get('/users/roles')

// --- Departments ---
export const getDepartments = (skip = 0, limit = 20, search = null, isActive = null) =>
  api.get('/departments/', { params: { skip, limit, search, is_active: isActive } })
export const getDepartment = (id) => api.get(`/departments/${id}`)
export const createDepartment = (data) => api.post('/departments/', data)
export const updateDepartment = (id, data) => api.put(`/departments/${id}`, data)
export const deleteDepartment = (id) => api.delete(`/departments/${id}`)
export const getDepartmentCourses = (id) => api.get(`/departments/${id}/courses`)
export const getDepartmentPrograms = (id) => api.get(`/departments/${id}/programs`)

// --- Courses ---
export const getCourses = (skip = 0, limit = 20, departmentId = null, search = null, isActive = null, courseLevel = null) =>
  api.get('/courses/', { params: { skip, limit, department_id: departmentId, search, is_active: isActive, course_level: courseLevel } })
export const getCourse = (id) => api.get(`/courses/${id}`)
export const createCourse = (data) => api.post('/courses/', data)
export const updateCourse = (id, data) => api.put(`/courses/${id}`, data)
export const deleteCourse = (id) => api.delete(`/courses/${id}`)
export const getCourseSections = (id, termId = null) => api.get(`/courses/${id}/sections`, { params: { term_id: termId } })

// --- Programs ---
export const getPrograms = (skip = 0, limit = 20, departmentId = null, degreeLevel = null, search = null, isActive = null) =>
  api.get('/programs/', { params: { skip, limit, department_id: departmentId, degree_level: degreeLevel, search, is_active: isActive } })
export const getProgram = (id) => api.get(`/programs/${id}`)
export const createProgram = (data) => api.post('/programs/', data)
export const updateProgram = (id, data) => api.put(`/programs/${id}`, data)
export const deleteProgram = (id) => api.delete(`/programs/${id}`)
export const getProgramStudents = (id) => api.get(`/programs/${id}/students`)

// --- Students ---
export const getStudents = (skip = 0, limit = 20, programId = null, enrollmentStatus = null, academicStanding = null, search = null, searchName = null, searchUsername = null, searchStudentNumber = null) =>
  api.get('/students/', { params: { skip, limit, program_id: programId, enrollment_status: enrollmentStatus, academic_standing: academicStanding, search, search_name: searchName, search_username: searchUsername, search_student_number: searchStudentNumber } })
export const getStudent = (id) => api.get(`/students/${id}`)
export const createStudent = (data) => api.post('/students/', data)
export const updateStudent = (id, data) => api.put(`/students/${id}`, data)
export const deleteStudent = (id) => api.delete(`/students/${id}`)
export const getStudentEnrollments = (id) => api.get(`/students/${id}/enrollments`)
export const getStudentAccount = (id) => api.get(`/students/${id}/account`)
export const getMyStudentProfile = () => api.get('/students/me')
export const getMyEnrollments = () => api.get('/students/me/enrollments')
export const getMyAssignments = () => api.get('/students/me/assignments')

// --- Faculty ---
export const getFaculty = (skip = 0, limit = 20, departmentId = null, employmentStatus = null, facultyRank = null, search = null) =>
  api.get('/faculty/', { params: { skip, limit, department_id: departmentId, employment_status: employmentStatus, faculty_rank: facultyRank, search } })
export const getFacultyById = (id) => api.get(`/faculty/${id}`)
export const createFaculty = (data) => api.post('/faculty/', data)
export const updateFaculty = (id, data) => api.put(`/faculty/${id}`, data)
export const deleteFaculty = (id) => api.delete(`/faculty/${id}`)
export const getFacultyProfile = () => api.get('/faculty/me')
export const getFacultySections = (id = 'me', termId = null) => api.get(id === 'me' ? '/faculty/me/sections' : `/faculty/${id}/sections`, { params: { term_id: termId } })
export const getFacultyAssignments = (id) => api.get(`/faculty/${id}/assignments`)

// --- Staff ---
export const getStaff = (skip = 0, limit = 20, departmentId = null, employmentStatus = null, jobCategory = null, search = null) =>
  api.get('/staff/', { params: { skip, limit, department_id: departmentId, employment_status: employmentStatus, job_category: jobCategory, search } })
export const getStaffMember = (id) => api.get(`/staff/${id}`)
export const createStaff = (data) => api.post('/staff/', data)
export const updateStaff = (id, data) => api.put(`/staff/${id}`, data)
export const deleteStaff = (id) => api.delete(`/staff/${id}`)

// --- Enrollments ---
export const getEnrollments = (skip = 0, limit = 20, studentId = null, sectionId = null, enrollmentStatus = null) =>
  api.get('/enrollments/', { params: { skip, limit, student_id: studentId, section_id: sectionId, enrollment_status: enrollmentStatus } })
export const getEnrollment = (id) => api.get(`/enrollments/${id}`)
export const createEnrollment = (data) => api.post('/enrollments/', data)
export const updateEnrollment = (id, data) => api.put(`/enrollments/${id}`, data)
export const deleteEnrollment = (id) => api.delete(`/enrollments/${id}`)
export const withdrawEnrollment = (id, reason = null) => api.post(`/enrollments/${id}/withdraw`, null, { params: { reason } })
export const submitGrade = (id, grade, gradePoints = null, gradedBy = null) =>
  api.post(`/enrollments/${id}/grade`, { grade, grade_points: gradePoints, graded_by: gradedBy })

// --- Academic Terms ---
export const getTerms = (skip = 0, limit = 20, academicYear = null, termType = null, status = null) =>
  api.get('/terms/', { params: { skip, limit, academic_year: academicYear, term_type: termType, status } })
export const getTerm = (id) => api.get(`/terms/${id}`)
export const createTerm = (data) => api.post('/terms/', data)
export const updateTerm = (id, data) => api.put(`/terms/${id}`, data)
export const deleteTerm = (id) => api.delete(`/terms/${id}`)
export const getCurrentTerm = () => api.get('/terms/current/active')
export const getUpcomingTerms = (skip = 0, limit = 5) => api.get('/terms/current/upcoming', { params: { skip, limit } })

// --- Course Sections ---
export const getSections = (skip = 0, limit = 20, course_id = null, term_id = null, instructor_id = null, status = null, delivery_mode = null) =>
  api.get('/sections/', { params: { skip, limit, course_id, term_id, instructor_id, status, delivery_mode } })
export const getSection = (id) => api.get(`/sections/${id}`)
export const createSection = (data) => api.post('/sections/', data)
export const updateSection = (id, data) => api.put(`/sections/${id}`, data)
export const deleteSection = (id) => api.delete(`/sections/${id}`)
export const getSectionEnrollments = (id, search = null) => api.get(`/sections/${id}/enrollments`, { params: { search } })
export const getSectionAssignments = (id) => api.get(`/sections/${id}/assignments`)

// --- Assignments & Submissions ---
export const getAssignments = (skip = 0, limit = 20, sectionId = null) => 
  api.get('/assignments/', { params: { skip, limit, section_id: sectionId } })
export const getAssignment = (id) => api.get(`/assignments/${id}`)
export const createAssignment = (data) => api.post('/assignments/', data)
export const updateAssignment = (id, data) => api.put(`/assignments/${id}`, data)
export const deleteAssignment = (id) => api.delete(`/assignments/${id}`)
export const getAssignmentSubmissions = (id) => api.get(`/assignments/${id}/submissions`)
export const submitAssignment = (id, data) => api.post(`/assignments/${id}/submit`, data)
export const getSubmission = (id) => api.get(`/submissions/${id}`)
export const gradeSubmission = (id, data) => api.post(`/submissions/${id}/grade`, data)

// --- Assignment Teams ---
export const createAssignmentTeam = (assignmentId, name) => api.post(`/assignments/${assignmentId}/teams`, null, { params: { name } })
export const getAssignmentTeams = (assignmentId) => api.get(`/assignments/${assignmentId}/teams`)
export const addTeamMember = (teamId, studentId) => api.post(`/assignments/teams/${teamId}/members`, null, { params: { student_id: studentId } })
export const removeTeamMember = (teamId, studentId) => api.delete(`/assignments/teams/${teamId}/members/${studentId}`)

// --- Enrollments ---
export const enrollStudent = (sectionId, studentId) => api.post(`/sections/${sectionId}/enroll`, null, { params: { student_id: studentId } })
export const joinSectionByCode = (joinCode, studentId) => api.post('/sections/join', { join_code: joinCode, student_id: studentId })
