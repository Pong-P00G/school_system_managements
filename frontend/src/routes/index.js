import { createRouter, createWebHistory } from 'vue-router'

import Dashboard from '../views/Dashboard.vue'
import Departments from '../views/Departments.vue'
import Courses from '../views/Courses.vue'
import Users from '../views/Users.vue'
import Programs from '../views/Programs.vue'
import Students from '../views/Students.vue'
import Lecturer from '../views/Lecturer.vue'
import Staff from '../views/Staff.vue'
import Terms from '../views/Terms.vue'
import Sections from '../views/Sections.vue'
import Enrollments from '../views/Enrollments.vue'
import StudentDashboard from '../views/student/Dashboard.vue'
import StudentCourses from '../views/student/Courses.vue'
import StudentAssignments from '../views/student/Assignments.vue'
import StudentGrades from '../views/student/Grades.vue'
import StudentSchedule from '../views/student/Schedule.vue'
import TeacherDashboard from '../views/teacher/Dashboard.vue'
import TeacherCourses from '../views/teacher/Courses.vue'
import TeacherStudents from '../views/teacher/Students.vue'
import TeacherGrades from '../views/teacher/Grades.vue'
import Login from '../views/auth/Login.vue'
import Register from '../views/auth/Register.vue'
import Unauthorized from '../views/Unauthorized.vue'
import NotFound from '../views/NotFound.vue'
import Notifications from '../views/Notifications.vue'
import StudentAttendance from '../views/student/Attendance.vue'
import Roles from '../views/admin/Roles.vue'
import TeacherAttendance from '../views/teacher/Attendance.vue'
import { useAuthStore } from '../stores/auth'


const routes = [
  { 
    path: '/login', 
    name: 'Login', 
    component: Login, 
    meta: { requiresAuth: false, title: 'Login' } 
  },
  { path: '/register', 
    name: 'Register', 
    component: Register, 
    meta: { requiresAuth: false, title: 'Register' } 
  },
  { path: '/unauthorized', 
    name: 'Unauthorized', 
    component: Unauthorized, 
    meta: { title: 'Access Denied' } 
  },  

  { 
    path: '/', 
    redirect: () => {
      try {
          const store = useAuthStore()
          const role = store.userRole
          if (role === 'student') return '/student/dashboard'
          if (role === 'teacher') return '/teacher/dashboard'
          return '/dashboard'
      } catch (e) {
          return '/dashboard'
      }
    } 
  },

  {
    path: '/',
    component: () => import('../layouts/DashboardLayout.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
    children: [
      { 
        path: 'dashboard', 
        name: 'Dashboard', 
        component: Dashboard, 
        meta: { title: 'Dashboard' } 
      },
      { 
        path: 'departments', 
        name: 'Departments', 
        component: Departments, 
        meta: { title: 'Departments' } 
      },
      { 
        path: 'courses', 
        name: 'Courses', 
        component: Courses, 
        meta: { title: 'Courses' } 
      },
      { 
        path: 'programs', 
        name: 'Programs', 
        component: Programs, 
        meta: { title: 'Programs' } 
      },
      { 
        path: 'users', 
        name: 'Users', 
        component: Users, 
        meta: { title: 'Users' } 
      },
      { 
        path: 'students', 
        name: 'Students', 
        component: Students, 
        meta: { title: 'Students' } 
      },
      { 
        path: 'lecturer', 
        name: 'Lecturer', 
        component: Lecturer, 
        meta: { title: 'Lecturer' } 
      },
      { 
        path: 'faculty/:id', 
        name: 'FacultyDetail', 
        component: () => import('../views/admin/FacultyDetail.vue'), 
        meta: { title: 'Faculty Details' } 
      },
      { 
        path: 'staff', 
        name: 'Staff', 
        component: Staff, 
        meta: { title: 'Staff' } 
      },
      { 
        path: 'terms', 
        name: 'Terms', 
        component: Terms, 
        meta: { title: 'Academic Terms' } 
      },
      { 
        path: 'sections', 
        name: 'Sections', 
        component: Sections, 
        meta: { title: 'Course Sections' } 
      },
      { 
        path: 'enrollments', 
        name: 'Enrollments', 
        component: Enrollments, 
        meta: { title: 'Enrollments' } 
      },
      { 
        path: '/admin/finance/program-fees', 
        name: 'ProgramFees', 
        component: () => import('../views/admin/ProgramFees.vue'), 
        meta: { title: 'Program Fees' } 
      },
      { 
        path: 'notifications', 
        name: 'Notifications', 
        component: Notifications, 
        meta: { title: 'Notifications' } 
      },
      { 
        path: 'attendance', 
        name: 'Attendance', 
        component: () => import('../views/teacher/Attendance.vue'), 
        meta: { title: 'Attendance' } 
      },
      { 
        path: 'roles', 
        name: 'Roles', 
        component: Roles, 
        meta: { title: 'Role Management' } 
      },
    ]
  },

  {
    path: '/student',
    component: () => import('../layouts/PortalLayout.vue'),
    meta: { requiresAuth: true, roles: ['student'] },
    children: [
      { 
        path: 'dashboard', 
        name: 'StudentDashboard', 
        component: StudentDashboard, 
        meta: { title: 'Student Dashboard' } 
      },
      { 
        path: 'courses', 
        name: 'StudentCourses', 
        component: StudentCourses, 
        meta: { title: 'My Courses' } 
      },
      { 
        path: 'assignments', 
        name: 'StudentAssignments', 
        component: StudentAssignments, 
        meta: { title: 'My Assignments' } 
      },
      { 
        path: 'grades', 
        name: 'StudentGrades', 
        component: StudentGrades, 
        meta: { title: 'My Grades' } 
      },
      { 
        path: 'schedule', 
        name: 'StudentSchedule', 
        component: StudentSchedule, 
        meta: { title: 'My Schedule' } 
      },
      { 
        path: 'notifications', 
        name: 'StudentNotifications', 
        component: Notifications, 
        meta: { title: 'Notifications' } 
      },
      { 
        path: 'attendance', 
        name: 'StudentAttendance', 
        component: StudentAttendance, 
        meta: { title: 'My Attendance' } 
      },
    ]
  },

  {
    path: '/teacher',
    component: () => import('../layouts/PortalLayout.vue'),
    meta: { requiresAuth: true, roles: ['teacher'] },
    children: [
      { 
        path: 'dashboard', 
        name: 'TeacherDashboard', 
        component: TeacherDashboard, 
        meta: { title: 'Teacher Dashboard' } 
      },
      { 
        path: 'courses', 
        name: 'TeacherCourses', 
        component: TeacherCourses, 
        meta: { title: 'My Courses' } 
      },
      { 
        path: 'students', 
        name: 'TeacherStudents', 
        component: TeacherStudents, 
        meta: { title: 'My Students' } 
      },
      { 
        path: 'grades', 
        name: 'TeacherGrades', 
        component: TeacherGrades, 
        meta: { title: 'Grade Management' } 
      },
      { 
        path: 'enrollment', 
        name: 'TeacherEnrollment', 
        component: () => import('../views/teacher/Enrollment.vue'), 
        meta: { title: 'Class Management' } 
      },
      { 
        path: 'attendance', 
        name: 'TeacherAttendance', 
        component: TeacherAttendance, 
        meta: { title: 'Attendance' } 
      },
      { 
        path: 'notifications', 
        name: 'TeacherNotifications', 
        component: Notifications, 
        meta: { title: 'Notifications' } 
      },
    ]
  },

  { path: '/:pathMatch(.*)*', 
    name: 'NotFound', 
    component: NotFound, 
    meta: { requiresAuth: false, title: 'Page Not Found' } 
  },
]

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior(to, from, savedPosition) {
    return { top: 0 }
  },
  routes,
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  const role = authStore.userRole || 'admin' 

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return next('/login')
  }

  if ((to.path === '/login' || to.path === '/register') && authStore.isAuthenticated) {
    // Redirect based on role
    if (role === 'student') next('/student/dashboard')
    else if (role === 'teacher') next('/teacher/dashboard')
    else next('/dashboard')
    return
  }

  if (to.meta.roles && authStore.isAuthenticated) {     
     let currentRole = role
     if (currentRole === 'faculty') currentRole = 'teacher'
     
     if (!to.meta.roles.includes(currentRole)) {
        next('/unauthorized')
        return
     }
  }
  next()
})

export default router
