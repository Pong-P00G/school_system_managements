-- ============================================================
--  School Management System - Full Database Schema
--  51 tables | PostgreSQL 18
--  Usage: psql -U <user> -d <dbname> -f schema.sql
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE FUNCTION calculate_student_gpa(p_student_id uuid, p_term_id integer DEFAULT NULL::integer) RETURNS TABLE(term_gpa numeric, cumulative_gpa numeric)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_term_gpa DECIMAL(3,2);
    v_cumulative_gpa DECIMAL(3,2);
BEGIN
    -- Calculate term GPA if term specified
    IF p_term_id IS NOT NULL THEN
        SELECT COALESCE(
            SUM(e.grade_points * c.credits) / NULLIF(SUM(c.credits), 0),
            0.00
        ) INTO v_term_gpa
        FROM enrollments e
        JOIN course_sections cs ON e.section_id = cs.section_id
        JOIN courses c ON cs.course_id = c.course_id
        WHERE e.student_id = p_student_id
        AND cs.term_id = p_term_id
        AND e.enrollment_status = 'completed'
        AND e.grade_points IS NOT NULL
        AND e.is_audit = false;
    END IF;
    
    -- Calculate cumulative GPA
    SELECT COALESCE(
        SUM(e.grade_points * c.credits) / NULLIF(SUM(c.credits), 0),
        0.00
    ) INTO v_cumulative_gpa
    FROM enrollments e
    JOIN course_sections cs ON e.section_id = cs.section_id
    JOIN courses c ON cs.course_id = c.course_id
    WHERE e.student_id = p_student_id
    AND e.enrollment_status = 'completed'
    AND e.grade_points IS NOT NULL
    AND e.is_audit = false;
    
    RETURN QUERY SELECT 
        ROUND(COALESCE(v_term_gpa, 0.00), 2),
        ROUND(COALESCE(v_cumulative_gpa, 0.00), 2);
END;
$$;

CREATE FUNCTION check_course_prerequisites(p_student_id uuid, p_course_id integer) RETURNS TABLE(all_prerequisites_met boolean, missing_prerequisites text[])
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_missing_prereqs TEXT[];
    v_all_met BOOLEAN;
BEGIN
    -- Get list of missing prerequisites
    SELECT ARRAY_AGG(c.course_code)
    INTO v_missing_prereqs
    FROM course_prerequisites cp
    JOIN courses c ON cp.prerequisite_course_id = c.course_id
    WHERE cp.course_id = p_course_id
    AND cp.is_mandatory = true
    AND NOT EXISTS (
        SELECT 1
        FROM enrollments e
        JOIN course_sections cs ON e.section_id = cs.section_id
        WHERE e.student_id = p_student_id
        AND cs.course_id = cp.prerequisite_course_id
        AND e.enrollment_status = 'completed'
        AND (cp.min_grade IS NULL OR e.grade_points >= 
            (SELECT grade_points FROM grade_scale_items WHERE letter_grade = cp.min_grade LIMIT 1))
    );
    
    -- Determine if all prerequisites are met
    v_all_met := (v_missing_prereqs IS NULL OR array_length(v_missing_prereqs, 1) = 0);
    
    RETURN QUERY SELECT v_all_met, COALESCE(v_missing_prereqs, ARRAY[]::TEXT[]);
END;
$$;

CREATE FUNCTION log_user_activity() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, new_values)
        VALUES (NEW.user_id, 'create', TG_TABLE_NAME, NEW.user_id::TEXT, to_jsonb(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, old_values, new_values)
        VALUES (NEW.user_id, 'update', TG_TABLE_NAME, NEW.user_id::TEXT, to_jsonb(OLD), to_jsonb(NEW));
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, old_values)
        VALUES (NULL, 'delete', TG_TABLE_NAME, OLD.user_id::TEXT, to_jsonb(OLD));
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$;

CREATE FUNCTION update_library_availability() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.checkout_status = 'checked_out' THEN
        UPDATE library_items
        SET available_copies = available_copies - 1
        WHERE item_id = NEW.item_id;
    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.checkout_status = 'checked_out' AND NEW.checkout_status IN ('returned', 'lost', 'damaged') THEN
            UPDATE library_items
            SET available_copies = available_copies + 1
            WHERE item_id = NEW.item_id;
        ELSIF OLD.checkout_status != 'checked_out' AND NEW.checkout_status = 'checked_out' THEN
            UPDATE library_items
            SET available_copies = available_copies - 1
            WHERE item_id = NEW.item_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE FUNCTION update_section_enrollment_count() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.enrollment_status = 'enrolled' THEN
        UPDATE course_sections 
        SET enrolled_count = enrolled_count + 1 
        WHERE section_id = NEW.section_id;
    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.enrollment_status = 'enrolled' AND NEW.enrollment_status != 'enrolled' THEN
            UPDATE course_sections 
            SET enrolled_count = enrolled_count - 1 
            WHERE section_id = NEW.section_id;
        ELSIF OLD.enrollment_status != 'enrolled' AND NEW.enrollment_status = 'enrolled' THEN
            UPDATE course_sections 
            SET enrolled_count = enrolled_count + 1 
            WHERE section_id = NEW.section_id;
        END IF;
    ELSIF TG_OP = 'DELETE' AND OLD.enrollment_status = 'enrolled' THEN
        UPDATE course_sections 
        SET enrolled_count = enrolled_count - 1 
        WHERE section_id = OLD.section_id;
    END IF;
    
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$;

CREATE FUNCTION update_student_account_balance() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.transaction_type IN ('charge') THEN
            UPDATE student_accounts 
            SET total_charges = total_charges + NEW.amount,
                balance = total_charges - total_payments - total_credits
            WHERE account_id = NEW.account_id;
        ELSIF NEW.transaction_type IN ('payment') THEN
            UPDATE student_accounts 
            SET total_payments = total_payments + NEW.amount,
                balance = total_charges - total_payments - total_credits
            WHERE account_id = NEW.account_id;
        ELSIF NEW.transaction_type IN ('refund', 'financial_aid', 'scholarship', 'waiver') THEN
            UPDATE student_accounts 
            SET total_credits = total_credits + NEW.amount,
                balance = total_charges - total_payments - total_credits
            WHERE account_id = NEW.account_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE FUNCTION update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TABLE academic_terms (
    term_id integer NOT NULL,
    term_name character varying(100) NOT NULL,
    term_code character varying(20) NOT NULL,
    academic_year character varying(9) NOT NULL,
    term_type character varying(20) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    registration_start_date date,
    registration_end_date date,
    add_drop_deadline date,
    withdrawal_deadline date,
    final_exam_start_date date,
    final_exam_end_date date,
    status character varying(20) DEFAULT 'upcoming'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_deadlines CHECK ((add_drop_deadline <= withdrawal_deadline)),
    CONSTRAINT chk_registration_dates CHECK ((registration_start_date <= registration_end_date)),
    CONSTRAINT chk_term_dates CHECK ((start_date < end_date)),
    CONSTRAINT chk_term_status CHECK (((status)::text = ANY ((ARRAY['upcoming'::character varying, 'registration_open'::character varying, 'active'::character varying, 'finals'::character varying, 'completed'::character varying, 'cancelled'::character varying])::text[]))),
    CONSTRAINT chk_term_type CHECK (((term_type)::text = ANY ((ARRAY['fall'::character varying, 'spring'::character varying, 'summer'::character varying, 'winter'::character varying, 'trimester'::character varying])::text[])))
);

CREATE SEQUENCE academic_terms_term_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE academic_terms_term_id_seq OWNED BY academic_terms.term_id;

CREATE TABLE alembic_version (
    version_num character varying(32) NOT NULL
);

CREATE TABLE announcements (
    announcement_id integer NOT NULL,
    title character varying(300) NOT NULL,
    content text NOT NULL,
    posted_by uuid NOT NULL,
    target_audience character varying(50) NOT NULL,
    department_id integer,
    program_id integer,
    priority character varying(20) DEFAULT 'normal'::character varying,
    start_datetime timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    end_datetime timestamp without time zone,
    is_active boolean DEFAULT true,
    view_count integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_priority CHECK (((priority)::text = ANY ((ARRAY['low'::character varying, 'normal'::character varying, 'high'::character varying, 'urgent'::character varying])::text[]))),
    CONSTRAINT chk_target_audience CHECK (((target_audience)::text = ANY ((ARRAY['all'::character varying, 'students'::character varying, 'faculty'::character varying, 'staff'::character varying, 'alumni'::character varying, 'department'::character varying, 'program'::character varying, 'specific_role'::character varying])::text[])))
);

CREATE SEQUENCE announcements_announcement_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE announcements_announcement_id_seq OWNED BY announcements.announcement_id;

CREATE TABLE assignment_submissions (
    submission_id integer NOT NULL,
    assignment_id integer NOT NULL,
    student_id uuid NOT NULL,
    submission_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    submission_url text,
    submission_text text,
    attachment_count integer DEFAULT 0,
    is_late boolean DEFAULT false,
    points_earned numeric(6,2),
    feedback text,
    graded_by uuid,
    graded_date timestamp without time zone,
    submission_status character varying(20) DEFAULT 'submitted'::character varying,
    attempts integer DEFAULT 1,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_points_valid CHECK (((points_earned IS NULL) OR (points_earned >= (0)::numeric))),
    CONSTRAINT chk_submission_status CHECK (((submission_status)::text = ANY ((ARRAY['draft'::character varying, 'submitted'::character varying, 'graded'::character varying, 'returned'::character varying, 'late'::character varying, 'missing'::character varying, 'excused'::character varying])::text[])))
);

CREATE SEQUENCE assignment_submissions_submission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE assignment_submissions_submission_id_seq OWNED BY assignment_submissions.submission_id;

CREATE TABLE assignments (
    assignment_id integer NOT NULL,
    section_id integer NOT NULL,
    assignment_name character varying(200) NOT NULL,
    assignment_type character varying(50) NOT NULL,
    description text,
    max_points numeric(6,2) NOT NULL,
    weight_percentage numeric(5,2),
    due_date timestamp without time zone,
    late_submission_allowed boolean DEFAULT false,
    late_penalty_percentage numeric(5,2),
    submission_type character varying(30),
    rubric_url text,
    is_published boolean DEFAULT false,
    is_group_assignment boolean DEFAULT false,
    created_by uuid NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_assignment_type CHECK (((assignment_type)::text = ANY ((ARRAY['homework'::character varying, 'quiz'::character varying, 'exam'::character varying, 'midterm'::character varying, 'final'::character varying, 'project'::character varying, 'presentation'::character varying, 'lab'::character varying, 'paper'::character varying, 'participation'::character varying, 'discussion'::character varying])::text[]))),
    CONSTRAINT chk_max_points_positive CHECK ((max_points > (0)::numeric)),
    CONSTRAINT chk_submission_type CHECK (((submission_type)::text = ANY ((ARRAY['online'::character varying, 'paper'::character varying, 'both'::character varying, 'none'::character varying])::text[]))),
    CONSTRAINT chk_weight_valid CHECK (((weight_percentage IS NULL) OR ((weight_percentage >= (0)::numeric) AND (weight_percentage <= (100)::numeric))))
);

CREATE SEQUENCE assignments_assignment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE assignments_assignment_id_seq OWNED BY assignments.assignment_id;

CREATE TABLE attendance (
    attendance_id integer NOT NULL,
    section_id integer NOT NULL,
    student_id uuid NOT NULL,
    class_date date NOT NULL,
    attendance_status character varying(20) NOT NULL,
    arrival_time time without time zone,
    notes text,
    recorded_by uuid NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_attendance_status CHECK (((attendance_status)::text = ANY ((ARRAY['present'::character varying, 'absent'::character varying, 'late'::character varying, 'excused'::character varying, 'tardy'::character varying])::text[])))
);

CREATE SEQUENCE attendance_attendance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE attendance_attendance_id_seq OWNED BY attendance.attendance_id;

CREATE TABLE audit_logs (
    log_id bigint NOT NULL,
    user_id uuid,
    action character varying(100) NOT NULL,
    entity_type character varying(100) NOT NULL,
    entity_id character varying(100),
    old_values jsonb,
    new_values jsonb,
    ip_address inet,
    user_agent text,
    session_id character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_action CHECK (((action)::text = ANY ((ARRAY['create'::character varying, 'read'::character varying, 'update'::character varying, 'delete'::character varying, 'login'::character varying, 'logout'::character varying, 'password_change'::character varying, 'password_reset'::character varying, 'email_verification'::character varying, 'role_change'::character varying, 'permission_change'::character varying])::text[])))
);

CREATE SEQUENCE audit_logs_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE audit_logs_log_id_seq OWNED BY audit_logs.log_id;

CREATE TABLE buildings (
    building_id integer NOT NULL,
    building_code character varying(10) NOT NULL,
    building_name character varying(200) NOT NULL,
    street_address character varying(255),
    city character varying(100),
    state character varying(100),
    postal_code character varying(20),
    total_floors integer,
    year_built integer,
    is_accessible boolean DEFAULT true,
    has_elevator boolean DEFAULT false,
    parking_available boolean DEFAULT false,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_floors_positive CHECK ((total_floors > 0)),
    CONSTRAINT chk_year_valid CHECK (((year_built >= 1800) AND ((year_built)::numeric <= EXTRACT(year FROM CURRENT_DATE))))
);

CREATE SEQUENCE buildings_building_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE buildings_building_id_seq OWNED BY buildings.building_id;

CREATE TABLE course_corequisites (
    corequisite_id integer NOT NULL,
    course_id integer NOT NULL,
    corequisite_course_id integer NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_not_self_corequisite CHECK ((course_id <> corequisite_course_id))
);

CREATE SEQUENCE course_corequisites_corequisite_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE course_corequisites_corequisite_id_seq OWNED BY course_corequisites.corequisite_id;

CREATE TABLE course_prerequisites (
    prerequisite_id integer NOT NULL,
    course_id integer NOT NULL,
    prerequisite_course_id integer NOT NULL,
    is_mandatory boolean DEFAULT true,
    min_grade character varying(5),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_not_self_prerequisite CHECK ((course_id <> prerequisite_course_id))
);

CREATE SEQUENCE course_prerequisites_prerequisite_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE course_prerequisites_prerequisite_id_seq OWNED BY course_prerequisites.prerequisite_id;

CREATE TABLE course_sections (
    section_id integer NOT NULL,
    course_id integer NOT NULL,
    term_id integer NOT NULL,
    section_number character varying(10) NOT NULL,
    instructor_id uuid,
    max_capacity integer NOT NULL,
    enrolled_count integer DEFAULT 0,
    waiting_list_count integer DEFAULT 0,
    room_id integer,
    schedule_pattern character varying(50),
    start_time time without time zone,
    end_time time without time zone,
    start_date date,
    end_date date,
    delivery_mode character varying(20) NOT NULL,
    meeting_url text,
    syllabus_url text,
    status character varying(20) DEFAULT 'planned'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_capacity_positive CHECK ((max_capacity > 0)),
    CONSTRAINT chk_delivery_mode CHECK (((delivery_mode)::text = ANY ((ARRAY['in-person'::character varying, 'online'::character varying, 'hybrid'::character varying, 'hyflex'::character varying])::text[]))),
    CONSTRAINT chk_enrolled_valid CHECK (((enrolled_count >= 0) AND (enrolled_count <= max_capacity))),
    CONSTRAINT chk_section_status CHECK (((status)::text = ANY ((ARRAY['planned'::character varying, 'open'::character varying, 'closed'::character varying, 'full'::character varying, 'cancelled'::character varying, 'completed'::character varying])::text[]))),
    CONSTRAINT chk_time_valid CHECK ((start_time < end_time))
);

CREATE SEQUENCE course_sections_section_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE course_sections_section_id_seq OWNED BY course_sections.section_id;

CREATE TABLE courses (
    course_id integer NOT NULL,
    course_code character varying(20) NOT NULL,
    course_name character varying(200) NOT NULL,
    department_id integer NOT NULL,
    credits integer NOT NULL,
    course_level character varying(20),
    lecture_hours numeric(4,2) DEFAULT 0,
    lab_hours numeric(4,2) DEFAULT 0,
    description text,
    learning_outcomes text,
    syllabus_url text,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_course_level CHECK (((course_level)::text = ANY ((ARRAY['100'::character varying, '200'::character varying, '300'::character varying, '400'::character varying, '500'::character varying, '600'::character varying, '700'::character varying, '800'::character varying])::text[]))),
    CONSTRAINT chk_credits_valid CHECK (((credits > 0) AND (credits <= 12))),
    CONSTRAINT chk_hours_positive CHECK (((lecture_hours >= (0)::numeric) AND (lab_hours >= (0)::numeric)))
);

CREATE SEQUENCE courses_course_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE courses_course_id_seq OWNED BY courses.course_id;

CREATE TABLE departments (
    department_id integer NOT NULL,
    department_code character varying(10) NOT NULL,
    department_name character varying(200) NOT NULL,
    description text,
    head_faculty_id uuid,
    parent_department_id integer,
    building character varying(100),
    phone character varying(20),
    email character varying(255),
    website_url character varying(500),
    established_date date,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE departments_department_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE departments_department_id_seq OWNED BY departments.department_id;

CREATE TABLE enrollments (
    enrollment_id integer NOT NULL,
    student_id uuid NOT NULL,
    section_id integer NOT NULL,
    enrollment_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    enrollment_status character varying(20) DEFAULT 'enrolled'::character varying,
    grade character varying(5),
    grade_points numeric(3,2),
    credits_earned integer DEFAULT 0,
    attendance_percentage numeric(5,2),
    midterm_grade character varying(5),
    final_grade character varying(5),
    grade_submitted_date timestamp without time zone,
    grade_submitted_by uuid,
    is_audit boolean DEFAULT false,
    withdrawal_date timestamp without time zone,
    withdrawal_reason text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_attendance CHECK (((attendance_percentage IS NULL) OR ((attendance_percentage >= 0.00) AND (attendance_percentage <= 100.00)))),
    CONSTRAINT chk_enrollment_status CHECK (((enrollment_status)::text = ANY ((ARRAY['enrolled'::character varying, 'dropped'::character varying, 'withdrawn'::character varying, 'completed'::character varying, 'failed'::character varying, 'incomplete'::character varying])::text[]))),
    CONSTRAINT chk_grade_points CHECK (((grade_points IS NULL) OR ((grade_points >= 0.00) AND (grade_points <= 4.00))))
);

CREATE SEQUENCE enrollments_enrollment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE enrollments_enrollment_id_seq OWNED BY enrollments.enrollment_id;

CREATE TABLE event_registrations (
    registration_id integer NOT NULL,
    event_id integer NOT NULL,
    user_id uuid NOT NULL,
    registration_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    payment_status character varying(20) DEFAULT 'not_required'::character varying,
    payment_date timestamp without time zone,
    attendance_status character varying(20) DEFAULT 'registered'::character varying,
    check_in_time timestamp without time zone,
    check_out_time timestamp without time zone,
    feedback_rating integer,
    feedback_comment text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_attendance_status CHECK (((attendance_status)::text = ANY ((ARRAY['registered'::character varying, 'confirmed'::character varying, 'attended'::character varying, 'no_show'::character varying, 'cancelled'::character varying, 'waitlisted'::character varying])::text[]))),
    CONSTRAINT chk_feedback_rating CHECK (((feedback_rating IS NULL) OR ((feedback_rating >= 1) AND (feedback_rating <= 5)))),
    CONSTRAINT chk_payment_status CHECK (((payment_status)::text = ANY ((ARRAY['not_required'::character varying, 'pending'::character varying, 'paid'::character varying, 'refunded'::character varying, 'waived'::character varying])::text[])))
);

CREATE SEQUENCE event_registrations_registration_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE event_registrations_registration_id_seq OWNED BY event_registrations.registration_id;

CREATE TABLE events (
    event_id integer NOT NULL,
    event_code character varying(20),
    event_name character varying(300) NOT NULL,
    event_type character varying(50) NOT NULL,
    description text,
    start_datetime timestamp without time zone NOT NULL,
    end_datetime timestamp without time zone NOT NULL,
    is_all_day boolean DEFAULT false,
    location character varying(200),
    room_id integer,
    virtual_meeting_url text,
    organizer_id uuid NOT NULL,
    department_id integer,
    max_participants integer,
    current_registrations integer DEFAULT 0,
    registration_required boolean DEFAULT false,
    registration_start_date timestamp without time zone,
    registration_deadline timestamp without time zone,
    registration_fee numeric(8,2) DEFAULT 0.00,
    is_public boolean DEFAULT true,
    event_status character varying(20) DEFAULT 'scheduled'::character varying,
    poster_url text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_event_dates CHECK ((end_datetime > start_datetime)),
    CONSTRAINT chk_event_status CHECK (((event_status)::text = ANY ((ARRAY['scheduled'::character varying, 'registration_open'::character varying, 'registration_closed'::character varying, 'ongoing'::character varying, 'completed'::character varying, 'cancelled'::character varying, 'postponed'::character varying])::text[]))),
    CONSTRAINT chk_event_type CHECK (((event_type)::text = ANY ((ARRAY['academic'::character varying, 'seminar'::character varying, 'workshop'::character varying, 'conference'::character varying, 'symposium'::character varying, 'lecture'::character varying, 'social'::character varying, 'sports'::character varying, 'cultural'::character varying, 'career_fair'::character varying, 'orientation'::character varying, 'meeting'::character varying, 'ceremony'::character varying, 'other'::character varying])::text[]))),
    CONSTRAINT chk_registration_capacity CHECK (((current_registrations >= 0) AND ((max_participants IS NULL) OR (current_registrations <= max_participants))))
);

CREATE SEQUENCE events_event_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE events_event_id_seq OWNED BY events.event_id;

CREATE TABLE faculty (
    faculty_id uuid NOT NULL,
    employee_number character varying(20) NOT NULL,
    department_id integer NOT NULL,
    hire_date date NOT NULL,
    termination_date date,
    faculty_rank character varying(50) NOT NULL,
    tenure_status character varying(30) NOT NULL,
    employment_type character varying(30) NOT NULL,
    employment_status character varying(20) DEFAULT 'active'::character varying,
    office_room_id integer,
    office_hours text,
    research_interests text,
    specializations text[],
    publications_count integer DEFAULT 0,
    teaching_load_credits integer DEFAULT 0,
    max_advisees integer DEFAULT 20,
    current_advisees integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_advisees_valid CHECK (((current_advisees >= 0) AND (current_advisees <= max_advisees))),
    CONSTRAINT chk_employment_status CHECK (((employment_status)::text = ANY ((ARRAY['active'::character varying, 'on_leave'::character varying, 'sabbatical'::character varying, 'retired'::character varying, 'terminated'::character varying])::text[]))),
    CONSTRAINT chk_employment_type CHECK (((employment_type)::text = ANY ((ARRAY['full-time'::character varying, 'part-time'::character varying, 'adjunct'::character varying, 'visiting'::character varying, 'temporary'::character varying])::text[]))),
    CONSTRAINT chk_faculty_rank CHECK (((faculty_rank)::text = ANY ((ARRAY['Instructor'::character varying, 'Lecturer'::character varying, 'Assistant Professor'::character varying, 'Associate Professor'::character varying, 'Professor'::character varying, 'Distinguished Professor'::character varying, 'Emeritus'::character varying, 'Adjunct'::character varying])::text[]))),
    CONSTRAINT chk_tenure_status CHECK (((tenure_status)::text = ANY ((ARRAY['non-tenure-track'::character varying, 'tenure-track'::character varying, 'tenured'::character varying, 'not-applicable'::character varying])::text[]))),
    CONSTRAINT chk_termination_after_hire CHECK (((termination_date IS NULL) OR (termination_date >= hire_date)))
);

CREATE TABLE faculty_publications (
    faculty_publication_id integer NOT NULL,
    faculty_id uuid NOT NULL,
    publication_id integer NOT NULL,
    author_order integer NOT NULL,
    is_corresponding_author boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_author_order_positive CHECK ((author_order > 0))
);

CREATE SEQUENCE faculty_publications_faculty_publication_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE faculty_publications_faculty_publication_id_seq OWNED BY faculty_publications.faculty_publication_id;

CREATE TABLE fee_structures (
    fee_structure_id integer NOT NULL,
    program_id integer,
    term_id integer,
    fee_type_id integer NOT NULL,
    amount numeric(10,2) NOT NULL,
    is_per_credit boolean DEFAULT false,
    is_mandatory boolean DEFAULT true,
    applies_to_international boolean DEFAULT true,
    applies_to_domestic boolean DEFAULT true,
    effective_date date NOT NULL,
    expiration_date date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_amount_positive CHECK ((amount >= (0)::numeric)),
    CONSTRAINT chk_date_range CHECK (((expiration_date IS NULL) OR (expiration_date > effective_date)))
);

CREATE SEQUENCE fee_structures_fee_structure_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE fee_structures_fee_structure_id_seq OWNED BY fee_structures.fee_structure_id;

CREATE TABLE fee_types (
    fee_type_id integer NOT NULL,
    fee_type_code character varying(20) NOT NULL,
    fee_type_name character varying(100) NOT NULL,
    description text,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_fee_type_code CHECK (((fee_type_code)::text = ANY ((ARRAY['tuition'::character varying, 'lab'::character varying, 'technology'::character varying, 'library'::character varying, 'student_activity'::character varying, 'health'::character varying, 'parking'::character varying, 'housing'::character varying, 'meal_plan'::character varying, 'registration'::character varying, 'late_payment'::character varying, 'other'::character varying])::text[])))
);

CREATE SEQUENCE fee_types_fee_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE fee_types_fee_type_id_seq OWNED BY fee_types.fee_type_id;

CREATE TABLE financial_transactions (
    transaction_id integer NOT NULL,
    account_id integer NOT NULL,
    term_id integer,
    transaction_type character varying(20) NOT NULL,
    transaction_category character varying(50),
    amount numeric(12,2) NOT NULL,
    description text,
    reference_number character varying(50),
    transaction_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    posted_date date,
    processed_by uuid NOT NULL,
    payment_method character varying(50),
    check_number character varying(20),
    card_last_four character varying(4),
    is_reversed boolean DEFAULT false,
    reversal_transaction_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_amount_nonzero CHECK ((amount <> (0)::numeric)),
    CONSTRAINT chk_payment_method CHECK ((((payment_method)::text = ANY ((ARRAY['cash'::character varying, 'check'::character varying, 'credit_card'::character varying, 'debit_card'::character varying, 'bank_transfer'::character varying, 'wire'::character varying, 'financial_aid'::character varying, 'scholarship'::character varying, 'other'::character varying])::text[])) OR (payment_method IS NULL))),
    CONSTRAINT chk_transaction_type CHECK (((transaction_type)::text = ANY ((ARRAY['charge'::character varying, 'payment'::character varying, 'refund'::character varying, 'adjustment'::character varying, 'financial_aid'::character varying, 'scholarship'::character varying, 'waiver'::character varying])::text[])))
);

CREATE SEQUENCE financial_transactions_transaction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE financial_transactions_transaction_id_seq OWNED BY financial_transactions.transaction_id;

CREATE TABLE grade_scale_items (
    item_id integer NOT NULL,
    scale_id integer NOT NULL,
    letter_grade character varying(5) NOT NULL,
    min_percentage numeric(5,2) NOT NULL,
    max_percentage numeric(5,2) NOT NULL,
    grade_points numeric(3,2) NOT NULL,
    CONSTRAINT chk_gp_range CHECK (((grade_points >= 0.00) AND (grade_points <= 4.00))),
    CONSTRAINT chk_percentage_range CHECK (((min_percentage >= (0)::numeric) AND (max_percentage <= (100)::numeric) AND (min_percentage < max_percentage)))
);

CREATE SEQUENCE grade_scale_items_item_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE grade_scale_items_item_id_seq OWNED BY grade_scale_items.item_id;

CREATE TABLE grade_scales (
    scale_id integer NOT NULL,
    scale_name character varying(100) NOT NULL,
    is_default boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE grade_scales_scale_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE grade_scales_scale_id_seq OWNED BY grade_scales.scale_id;

CREATE TABLE library_checkouts (
    checkout_id integer NOT NULL,
    item_id integer NOT NULL,
    user_id uuid NOT NULL,
    checkout_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    due_date timestamp without time zone NOT NULL,
    return_date timestamp without time zone,
    renewed_count integer DEFAULT 0,
    fine_amount numeric(8,2) DEFAULT 0.00,
    fine_paid boolean DEFAULT false,
    checkout_status character varying(20) DEFAULT 'checked_out'::character varying,
    checkout_location character varying(100),
    return_location character varying(100),
    checked_out_by uuid NOT NULL,
    checked_in_by uuid,
    notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_checkout_status CHECK (((checkout_status)::text = ANY ((ARRAY['checked_out'::character varying, 'returned'::character varying, 'overdue'::character varying, 'lost'::character varying, 'damaged'::character varying])::text[]))),
    CONSTRAINT chk_fine_nonnegative CHECK ((fine_amount >= (0)::numeric)),
    CONSTRAINT chk_return_after_checkout CHECK (((return_date IS NULL) OR (return_date >= checkout_date)))
);

CREATE SEQUENCE library_checkouts_checkout_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE library_checkouts_checkout_id_seq OWNED BY library_checkouts.checkout_id;

CREATE TABLE library_items (
    item_id integer NOT NULL,
    item_type character varying(50) NOT NULL,
    isbn character varying(20),
    issn character varying(20),
    title character varying(500) NOT NULL,
    subtitle character varying(500),
    author character varying(300),
    co_authors text[],
    publisher character varying(200),
    publication_year integer,
    edition character varying(50),
    volume character varying(50),
    series character varying(200),
    language character varying(50) DEFAULT 'English'::character varying,
    category character varying(100),
    subject_headings text[],
    call_number character varying(50),
    location character varying(100),
    total_copies integer DEFAULT 1,
    available_copies integer DEFAULT 1,
    checkout_period_days integer DEFAULT 14,
    renewable boolean DEFAULT true,
    max_renewals integer DEFAULT 2,
    item_status character varying(20) DEFAULT 'available'::character varying,
    purchase_date date,
    purchase_price numeric(10,2),
    condition_notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_copies_valid CHECK (((available_copies >= 0) AND (available_copies <= total_copies))),
    CONSTRAINT chk_item_status CHECK (((item_status)::text = ANY ((ARRAY['available'::character varying, 'checked_out'::character varying, 'reserved'::character varying, 'lost'::character varying, 'damaged'::character varying, 'in_repair'::character varying, 'withdrawn'::character varying])::text[]))),
    CONSTRAINT chk_item_type CHECK (((item_type)::text = ANY ((ARRAY['book'::character varying, 'ebook'::character varying, 'journal'::character varying, 'magazine'::character varying, 'newspaper'::character varying, 'thesis'::character varying, 'dissertation'::character varying, 'dvd'::character varying, 'audio'::character varying, 'database'::character varying, 'reference'::character varying, 'periodical'::character varying])::text[]))),
    CONSTRAINT chk_publication_year CHECK (((publication_year IS NULL) OR ((publication_year >= 1000) AND ((publication_year)::numeric <= (EXTRACT(year FROM CURRENT_DATE) + (1)::numeric)))))
);

CREATE SEQUENCE library_items_item_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE library_items_item_id_seq OWNED BY library_items.item_id;

CREATE TABLE library_reservations (
    reservation_id integer NOT NULL,
    item_id integer NOT NULL,
    user_id uuid NOT NULL,
    reservation_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    expiration_date timestamp without time zone NOT NULL,
    notification_sent boolean DEFAULT false,
    reservation_status character varying(20) DEFAULT 'active'::character varying,
    fulfilled_date timestamp without time zone,
    cancelled_date timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_reserve_status CHECK (((reservation_status)::text = ANY ((ARRAY['active'::character varying, 'notified'::character varying, 'fulfilled'::character varying, 'expired'::character varying, 'cancelled'::character varying])::text[])))
);

CREATE SEQUENCE library_reservations_reservation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE library_reservations_reservation_id_seq OWNED BY library_reservations.reservation_id;

CREATE TABLE notifications (
    notification_id integer NOT NULL,
    user_id uuid NOT NULL,
    notification_type character varying(50) NOT NULL,
    title character varying(200) NOT NULL,
    message text NOT NULL,
    link_url text,
    is_read boolean DEFAULT false,
    read_at timestamp without time zone,
    is_actionable boolean DEFAULT false,
    action_taken boolean DEFAULT false,
    action_url text,
    priority character varying(20) DEFAULT 'normal'::character varying,
    expires_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    reference_type character varying(50),
    reference_id character varying(50),
    CONSTRAINT chk_notif_priority CHECK (((priority)::text = ANY ((ARRAY['low'::character varying, 'normal'::character varying, 'high'::character varying, 'urgent'::character varying])::text[]))),
    CONSTRAINT chk_notif_type CHECK (((notification_type)::text = ANY ((ARRAY['enrollment'::character varying, 'grade'::character varying, 'payment'::character varying, 'financial_aid'::character varying, 'event'::character varying, 'announcement'::character varying, 'deadline'::character varying, 'message'::character varying, 'alert'::character varying, 'reminder'::character varying, 'system'::character varying])::text[])))
);

CREATE SEQUENCE notifications_notification_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE notifications_notification_id_seq OWNED BY notifications.notification_id;

CREATE TABLE organization_members (
    membership_id integer NOT NULL,
    organization_id integer NOT NULL,
    student_id uuid NOT NULL,
    member_role character varying(50) DEFAULT 'member'::character varying,
    join_date date NOT NULL,
    end_date date,
    membership_status character varying(20) DEFAULT 'active'::character varying,
    dues_paid boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_member_role CHECK (((member_role)::text = ANY ((ARRAY['member'::character varying, 'officer'::character varying, 'treasurer'::character varying, 'secretary'::character varying, 'vice_president'::character varying, 'president'::character varying, 'founder'::character varying])::text[]))),
    CONSTRAINT chk_membership_dates CHECK (((end_date IS NULL) OR (end_date >= join_date))),
    CONSTRAINT chk_membership_status CHECK (((membership_status)::text = ANY ((ARRAY['active'::character varying, 'inactive'::character varying, 'suspended'::character varying, 'alumni'::character varying])::text[])))
);

CREATE SEQUENCE organization_members_membership_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE organization_members_membership_id_seq OWNED BY organization_members.membership_id;

CREATE TABLE organizations (
    organization_id integer NOT NULL,
    organization_code character varying(20) NOT NULL,
    organization_name character varying(200) NOT NULL,
    organization_type character varying(50) NOT NULL,
    description text,
    mission_statement text,
    advisor_id uuid,
    president_id uuid,
    department_id integer,
    founded_date date,
    email character varying(255),
    website_url character varying(500),
    meeting_schedule text,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_org_type CHECK (((organization_type)::text = ANY ((ARRAY['academic'::character varying, 'professional'::character varying, 'cultural'::character varying, 'social'::character varying, 'sports'::character varying, 'service'::character varying, 'honorary'::character varying, 'religious'::character varying, 'political'::character varying, 'special_interest'::character varying])::text[])))
);

CREATE SEQUENCE organizations_organization_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE organizations_organization_id_seq OWNED BY organizations.organization_id;

CREATE TABLE programs (
    program_id integer NOT NULL,
    program_code character varying(20) NOT NULL,
    program_name character varying(200) NOT NULL,
    department_id integer NOT NULL,
    degree_level character varying(50) NOT NULL,
    duration_years numeric(3,1),
    total_credits_required integer NOT NULL,
    description text,
    coordinator_id uuid,
    accreditation_status character varying(50),
    accreditation_body character varying(200),
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_credits_positive CHECK ((total_credits_required > 0)),
    CONSTRAINT chk_degree_level CHECK (((degree_level)::text = ANY ((ARRAY['Certificate'::character varying, 'Associate'::character varying, 'Bachelor'::character varying, 'Master'::character varying, 'Doctorate'::character varying, 'Post-Doctorate'::character varying])::text[])))
);

CREATE SEQUENCE programs_program_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE programs_program_id_seq OWNED BY programs.program_id;

CREATE TABLE publications (
    publication_id integer NOT NULL,
    publication_type character varying(50) NOT NULL,
    title character varying(500) NOT NULL,
    authors text NOT NULL,
    venue character varying(300),
    publisher character varying(200),
    publication_date date,
    volume character varying(20),
    issue character varying(20),
    pages character varying(50),
    doi character varying(100),
    isbn character varying(20),
    url text,
    abstract text,
    keywords text[],
    citation_count integer DEFAULT 0,
    is_peer_reviewed boolean DEFAULT false,
    project_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_publication_type CHECK (((publication_type)::text = ANY ((ARRAY['journal'::character varying, 'conference'::character varying, 'book'::character varying, 'book_chapter'::character varying, 'patent'::character varying, 'thesis'::character varying, 'dissertation'::character varying, 'working_paper'::character varying, 'technical_report'::character varying, 'poster'::character varying, 'presentation'::character varying])::text[])))
);

CREATE SEQUENCE publications_publication_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE publications_publication_id_seq OWNED BY publications.publication_id;

CREATE TABLE research_projects (
    project_id integer NOT NULL,
    project_code character varying(20) NOT NULL,
    project_title character varying(500) NOT NULL,
    principal_investigator_id uuid NOT NULL,
    department_id integer NOT NULL,
    project_type character varying(50) NOT NULL,
    start_date date NOT NULL,
    end_date date,
    actual_end_date date,
    funding_amount numeric(15,2),
    funding_source character varying(200),
    grant_number character varying(100),
    project_status character varying(50) DEFAULT 'planning'::character varying,
    description text,
    objectives text,
    methodology text,
    keywords text[],
    irb_approved boolean DEFAULT false,
    irb_approval_number character varying(50),
    irb_approval_date date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_project_dates CHECK (((end_date IS NULL) OR (end_date >= start_date))),
    CONSTRAINT chk_project_status CHECK (((project_status)::text = ANY ((ARRAY['planning'::character varying, 'proposal'::character varying, 'approved'::character varying, 'active'::character varying, 'on_hold'::character varying, 'completed'::character varying, 'cancelled'::character varying, 'archived'::character varying])::text[]))),
    CONSTRAINT chk_project_type CHECK (((project_type)::text = ANY ((ARRAY['basic_research'::character varying, 'applied_research'::character varying, 'development'::character varying, 'consulting'::character varying, 'service'::character varying])::text[])))
);

CREATE SEQUENCE research_projects_project_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE research_projects_project_id_seq OWNED BY research_projects.project_id;

CREATE TABLE research_team_members (
    member_id integer NOT NULL,
    project_id integer NOT NULL,
    user_id uuid NOT NULL,
    role character varying(50) NOT NULL,
    start_date date NOT NULL,
    end_date date,
    contribution_percentage numeric(5,2),
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_contribution CHECK (((contribution_percentage IS NULL) OR ((contribution_percentage >= (0)::numeric) AND (contribution_percentage <= (100)::numeric)))),
    CONSTRAINT chk_team_role CHECK (((role)::text = ANY ((ARRAY['principal_investigator'::character varying, 'co_investigator'::character varying, 'senior_researcher'::character varying, 'research_assistant'::character varying, 'graduate_assistant'::character varying, 'undergraduate_assistant'::character varying, 'postdoc'::character varying, 'collaborator'::character varying, 'consultant'::character varying])::text[])))
);

CREATE SEQUENCE research_team_members_member_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE research_team_members_member_id_seq OWNED BY research_team_members.member_id;

CREATE TABLE reviews (
    review_id integer NOT NULL,
    enrollment_id integer NOT NULL,
    course_id integer,
    faculty_id uuid,
    term_id integer,
    overall_rating integer NOT NULL,
    teaching_rating integer,
    content_rating integer,
    workload_rating integer,
    title character varying(200),
    comment text,
    is_anonymous boolean NOT NULL,
    is_approved boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);

CREATE SEQUENCE reviews_review_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE reviews_review_id_seq OWNED BY reviews.review_id;

CREATE TABLE rooms (
    room_id integer NOT NULL,
    building_id integer NOT NULL,
    room_number character varying(20) NOT NULL,
    room_name character varying(100),
    room_type character varying(50) NOT NULL,
    floor_number integer,
    capacity integer,
    area_sqft numeric(10,2),
    features text[],
    equipment text[],
    is_accessible boolean DEFAULT true,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_capacity_positive CHECK ((capacity > 0)),
    CONSTRAINT chk_room_type CHECK (((room_type)::text = ANY ((ARRAY['classroom'::character varying, 'lecture_hall'::character varying, 'lab'::character varying, 'computer_lab'::character varying, 'seminar'::character varying, 'office'::character varying, 'auditorium'::character varying, 'library'::character varying, 'study_room'::character varying, 'conference'::character varying])::text[])))
);

CREATE SEQUENCE rooms_room_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE rooms_room_id_seq OWNED BY rooms.room_id;

CREATE TABLE scholarship_awards (
    award_id integer NOT NULL,
    scholarship_id integer NOT NULL,
    student_id uuid NOT NULL,
    term_id integer NOT NULL,
    award_amount numeric(10,2) NOT NULL,
    award_date date NOT NULL,
    disbursement_date date,
    disbursement_amount numeric(10,2),
    award_status character varying(20) DEFAULT 'pending'::character varying,
    renewal_number integer DEFAULT 0,
    conditions text,
    notes text,
    approved_by uuid,
    approval_date date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_award_amount_positive CHECK ((award_amount > (0)::numeric)),
    CONSTRAINT chk_award_status CHECK (((award_status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'disbursed'::character varying, 'partially_disbursed'::character varying, 'cancelled'::character varying, 'revoked'::character varying])::text[]))),
    CONSTRAINT chk_disbursement_valid CHECK (((disbursement_amount IS NULL) OR (disbursement_amount <= award_amount)))
);

CREATE SEQUENCE scholarship_awards_award_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE scholarship_awards_award_id_seq OWNED BY scholarship_awards.award_id;

CREATE TABLE scholarships (
    scholarship_id integer NOT NULL,
    scholarship_code character varying(20) NOT NULL,
    scholarship_name character varying(200) NOT NULL,
    description text,
    scholarship_type character varying(50) NOT NULL,
    sponsor_name character varying(200),
    total_annual_budget numeric(12,2),
    individual_award_min numeric(10,2),
    individual_award_max numeric(10,2),
    eligibility_criteria text,
    required_gpa numeric(3,2),
    required_credits integer,
    application_required boolean DEFAULT true,
    application_deadline date,
    is_renewable boolean DEFAULT false,
    max_renewals integer,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_award_range CHECK ((individual_award_max >= individual_award_min)),
    CONSTRAINT chk_scholarship_type CHECK (((scholarship_type)::text = ANY ((ARRAY['merit'::character varying, 'need-based'::character varying, 'athletic'::character varying, 'departmental'::character varying, 'diversity'::character varying, 'external'::character varying, 'endowed'::character varying, 'general'::character varying])::text[])))
);

CREATE SEQUENCE scholarships_scholarship_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE scholarships_scholarship_id_seq OWNED BY scholarships.scholarship_id;

CREATE TABLE staff (
    staff_id uuid NOT NULL,
    employee_number character varying(20) NOT NULL,
    department_id integer,
    hire_date date NOT NULL,
    termination_date date,
    job_title character varying(200) NOT NULL,
    job_category character varying(50) NOT NULL,
    employment_type character varying(30) NOT NULL,
    employment_status character varying(20) DEFAULT 'active'::character varying,
    office_room_id integer,
    supervisor_id uuid,
    salary_grade character varying(10),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_job_category CHECK (((job_category)::text = ANY ((ARRAY['administrative'::character varying, 'technical'::character varying, 'support'::character varying, 'maintenance'::character varying, 'security'::character varying, 'healthcare'::character varying, 'other'::character varying])::text[]))),
    CONSTRAINT chk_staff_employment_status CHECK (((employment_status)::text = ANY ((ARRAY['active'::character varying, 'on_leave'::character varying, 'terminated'::character varying, 'retired'::character varying])::text[]))),
    CONSTRAINT chk_staff_employment_type CHECK (((employment_type)::text = ANY ((ARRAY['full-time'::character varying, 'part-time'::character varying, 'temporary'::character varying, 'contract'::character varying])::text[]))),
    CONSTRAINT chk_staff_termination CHECK (((termination_date IS NULL) OR (termination_date >= hire_date)))
);

CREATE TABLE student_accounts (
    account_id integer NOT NULL,
    student_id uuid NOT NULL,
    account_number character varying(20) NOT NULL,
    total_charges numeric(12,2) DEFAULT 0.00,
    total_payments numeric(12,2) DEFAULT 0.00,
    total_credits numeric(12,2) DEFAULT 0.00,
    balance numeric(12,2) DEFAULT 0.00,
    has_hold boolean DEFAULT false,
    hold_reason text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_balance_calculation CHECK ((balance = ((total_charges - total_payments) - total_credits)))
);

CREATE SEQUENCE student_accounts_account_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE student_accounts_account_id_seq OWNED BY student_accounts.account_id;

CREATE TABLE students (
    student_id uuid NOT NULL,
    student_number character varying(20) NOT NULL,
    program_id integer NOT NULL,
    enrollment_date date NOT NULL,
    expected_graduation_date date,
    actual_graduation_date date,
    current_term_id integer,
    academic_standing character varying(50) DEFAULT 'good_standing'::character varying,
    enrollment_status character varying(50) DEFAULT 'active'::character varying,
    gpa numeric(3,2) DEFAULT 0.00,
    cumulative_gpa numeric(3,2) DEFAULT 0.00,
    total_credits_earned integer DEFAULT 0,
    total_credits_attempted integer DEFAULT 0,
    advisor_id uuid,
    admission_type character varying(50),
    is_international boolean DEFAULT false,
    visa_type character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_academic_standing CHECK (((academic_standing)::text = ANY ((ARRAY['good_standing'::character varying, 'probation'::character varying, 'suspension'::character varying, 'dismissal'::character varying, 'honors'::character varying, 'deans_list'::character varying])::text[]))),
    CONSTRAINT chk_credits_valid CHECK (((total_credits_earned >= 0) AND (total_credits_attempted >= total_credits_earned))),
    CONSTRAINT chk_cumulative_gpa_range CHECK (((cumulative_gpa >= 0.00) AND (cumulative_gpa <= 4.00))),
    CONSTRAINT chk_enrollment_status CHECK (((enrollment_status)::text = ANY ((ARRAY['active'::character varying, 'inactive'::character varying, 'leave_of_absence'::character varying, 'graduated'::character varying, 'withdrawn'::character varying, 'dismissed'::character varying, 'transferred'::character varying])::text[]))),
    CONSTRAINT chk_gpa_range CHECK (((gpa >= 0.00) AND (gpa <= 4.00))),
    CONSTRAINT chk_graduation_dates CHECK (((actual_graduation_date IS NULL) OR (actual_graduation_date >= enrollment_date)))
);

CREATE TABLE system_settings (
    setting_id integer NOT NULL,
    setting_key character varying(100) NOT NULL,
    setting_value text NOT NULL,
    setting_type character varying(20) NOT NULL,
    description text,
    is_editable boolean DEFAULT true,
    last_modified_by uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_setting_type CHECK (((setting_type)::text = ANY ((ARRAY['string'::character varying, 'integer'::character varying, 'decimal'::character varying, 'boolean'::character varying, 'json'::character varying, 'date'::character varying, 'datetime'::character varying])::text[])))
);

CREATE SEQUENCE system_settings_setting_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE system_settings_setting_id_seq OWNED BY system_settings.setting_id;

CREATE TABLE user_addresses (
    address_id integer NOT NULL,
    user_id uuid NOT NULL,
    address_type character varying(20) NOT NULL,
    street_address_1 character varying(255),
    street_address_2 character varying(255),
    city character varying(100),
    state_province character varying(100),
    postal_code character varying(20),
    country character varying(100) DEFAULT 'USA'::character varying,
    is_primary boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_address_type CHECK (((address_type)::text = ANY ((ARRAY['permanent'::character varying, 'mailing'::character varying, 'temporary'::character varying, 'billing'::character varying])::text[])))
);

CREATE SEQUENCE user_addresses_address_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE user_addresses_address_id_seq OWNED BY user_addresses.address_id;

CREATE TABLE user_contact_info (
    contact_id integer NOT NULL,
    user_id uuid NOT NULL,
    contact_type character varying(20) NOT NULL,
    contact_value text NOT NULL,
    is_primary boolean DEFAULT false,
    is_verified boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_contact_type CHECK (((contact_type)::text = ANY ((ARRAY['phone'::character varying, 'mobile'::character varying, 'work_phone'::character varying, 'home_phone'::character varying, 'email'::character varying, 'alternate_email'::character varying])::text[])))
);

CREATE SEQUENCE user_contact_info_contact_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE user_contact_info_contact_id_seq OWNED BY user_contact_info.contact_id;

CREATE TABLE user_emergency_contacts (
    emergency_contact_id integer NOT NULL,
    user_id uuid NOT NULL,
    contact_name character varying(200) NOT NULL,
    relationship character varying(50) NOT NULL,
    phone_number character varying(20) NOT NULL,
    alternate_phone character varying(20),
    email character varying(255),
    address text,
    is_primary boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_relationship CHECK (((relationship)::text = ANY ((ARRAY['parent'::character varying, 'guardian'::character varying, 'spouse'::character varying, 'sibling'::character varying, 'friend'::character varying, 'other'::character varying])::text[])))
);

CREATE SEQUENCE user_emergency_contacts_emergency_contact_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE user_emergency_contacts_emergency_contact_id_seq OWNED BY user_emergency_contacts.emergency_contact_id;

CREATE TABLE user_personal_info (
    info_id integer NOT NULL,
    user_id uuid NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    middle_name character varying(100),
    preferred_name character varying(100),
    date_of_birth date,
    gender character varying(20),
    nationality character varying(100),
    ssn_encrypted text,
    profile_picture_url text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_dob CHECK ((date_of_birth <= (CURRENT_DATE - '13 years'::interval))),
    CONSTRAINT chk_gender CHECK (((gender)::text = ANY ((ARRAY['male'::character varying, 'female'::character varying, 'non-binary'::character varying, 'prefer_not_to_say'::character varying, 'other'::character varying])::text[])))
);

CREATE SEQUENCE user_personal_info_info_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE user_personal_info_info_id_seq OWNED BY user_personal_info.info_id;

CREATE TABLE user_preferences (
    preference_id integer NOT NULL,
    user_id uuid NOT NULL,
    language character varying(10) DEFAULT 'en'::character varying,
    timezone character varying(50) DEFAULT 'UTC'::character varying,
    date_format character varying(20) DEFAULT 'YYYY-MM-DD'::character varying,
    notification_email boolean DEFAULT true,
    notification_sms boolean DEFAULT false,
    notification_push boolean DEFAULT true,
    theme character varying(20) DEFAULT 'light'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_theme CHECK (((theme)::text = ANY ((ARRAY['light'::character varying, 'dark'::character varying, 'auto'::character varying])::text[])))
);

CREATE SEQUENCE user_preferences_preference_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE user_preferences_preference_id_seq OWNED BY user_preferences.preference_id;

CREATE TABLE user_role_assignments (
    assignment_id integer NOT NULL,
    user_id uuid NOT NULL,
    role_id integer NOT NULL,
    assigned_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    assigned_by uuid,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE user_role_assignments_assignment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE user_role_assignments_assignment_id_seq OWNED BY user_role_assignments.assignment_id;

CREATE TABLE user_roles (
    role_id integer NOT NULL,
    role_name character varying(50) NOT NULL,
    description text,
    is_system_role boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE user_roles_role_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE user_roles_role_id_seq OWNED BY user_roles.role_id;

CREATE TABLE user_sessions (
    session_id character varying(100) NOT NULL,
    user_id uuid NOT NULL,
    ip_address inet,
    user_agent text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamp without time zone NOT NULL,
    last_activity timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_active boolean DEFAULT true
);

CREATE TABLE users (
    user_id uuid DEFAULT uuid_generate_v4() NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    is_active boolean DEFAULT true,
    is_verified boolean DEFAULT false,
    last_login timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_email_format CHECK (((email)::text ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'::text))
);

CREATE VIEW v_current_enrollments AS
 SELECT e.enrollment_id,
    s.student_number,
    concat(upi.first_name, ' ', upi.last_name) AS student_name,
    c.course_code,
    c.course_name,
    c.credits,
    cs.section_number,
    at.term_name,
    at.academic_year,
    concat(fupi.first_name, ' ', fupi.last_name) AS instructor_name,
    cs.schedule_pattern,
    cs.start_time,
    cs.end_time,
    cs.delivery_mode,
    r.room_number,
    b.building_name,
    e.enrollment_status,
    e.grade,
    e.grade_points
   FROM ((((((((((enrollments e
     JOIN students s ON ((e.student_id = s.student_id)))
     JOIN users u ON ((s.student_id = u.user_id)))
     JOIN user_personal_info upi ON ((u.user_id = upi.user_id)))
     JOIN course_sections cs ON ((e.section_id = cs.section_id)))
     JOIN courses c ON ((cs.course_id = c.course_id)))
     JOIN academic_terms at ON ((cs.term_id = at.term_id)))
     LEFT JOIN users fu ON ((cs.instructor_id = fu.user_id)))
     LEFT JOIN user_personal_info fupi ON ((fu.user_id = fupi.user_id)))
     LEFT JOIN rooms r ON ((cs.room_id = r.room_id)))
     LEFT JOIN buildings b ON ((r.building_id = b.building_id)));

CREATE VIEW v_faculty_teaching_schedule AS
 SELECT f.faculty_id,
    f.employee_number,
    concat(upi.first_name, ' ', upi.last_name) AS faculty_name,
    d.department_name,
    f.faculty_rank,
    at.term_name,
    at.academic_year,
    c.course_code,
    c.course_name,
    c.credits,
    cs.section_number,
    cs.schedule_pattern,
    cs.start_time,
    cs.end_time,
    cs.delivery_mode,
    b.building_name,
    r.room_number,
    cs.enrolled_count,
    cs.max_capacity,
    round((((cs.enrolled_count)::numeric / (cs.max_capacity)::numeric) * (100)::numeric), 2) AS capacity_percentage
   FROM ((((((((faculty f
     JOIN users u ON ((f.faculty_id = u.user_id)))
     JOIN user_personal_info upi ON ((u.user_id = upi.user_id)))
     JOIN departments d ON ((f.department_id = d.department_id)))
     JOIN course_sections cs ON ((f.faculty_id = cs.instructor_id)))
     JOIN courses c ON ((cs.course_id = c.course_id)))
     JOIN academic_terms at ON ((cs.term_id = at.term_id)))
     LEFT JOIN rooms r ON ((cs.room_id = r.room_id)))
     LEFT JOIN buildings b ON ((r.building_id = b.building_id)));

CREATE VIEW v_student_academic_summary AS
 SELECT s.student_id,
    s.student_number,
    upi.first_name,
    upi.last_name,
    concat(upi.first_name, ' ', upi.last_name) AS full_name,
    p.program_name,
    p.degree_level,
    d.department_name,
    s.gpa,
    s.cumulative_gpa,
    s.total_credits_earned,
    s.total_credits_attempted,
    p.total_credits_required,
    (p.total_credits_required - s.total_credits_earned) AS credits_remaining,
    s.academic_standing,
    s.enrollment_status,
    s.enrollment_date,
    s.expected_graduation_date,
    at.term_name AS current_term,
    concat(adv.first_name, ' ', adv.last_name) AS advisor_name
   FROM (((((((students s
     JOIN users u ON ((s.student_id = u.user_id)))
     JOIN user_personal_info upi ON ((u.user_id = upi.user_id)))
     JOIN programs p ON ((s.program_id = p.program_id)))
     JOIN departments d ON ((p.department_id = d.department_id)))
     LEFT JOIN academic_terms at ON ((s.current_term_id = at.term_id)))
     LEFT JOIN users advu ON ((s.advisor_id = advu.user_id)))
     LEFT JOIN user_personal_info adv ON ((advu.user_id = adv.user_id)));

CREATE VIEW v_student_financial_status AS
 SELECT s.student_id,
    s.student_number,
    concat(upi.first_name, ' ', upi.last_name) AS student_name,
    sa.account_number,
    sa.total_charges,
    sa.total_payments,
    sa.total_credits,
    sa.balance,
    sa.has_hold,
    sa.hold_reason,
        CASE
            WHEN (sa.balance > (0)::numeric) THEN 'Outstanding'::text
            WHEN (sa.balance = (0)::numeric) THEN 'Paid'::text
            ELSE 'Credit'::text
        END AS payment_status,
    s.enrollment_status
   FROM (((students s
     JOIN users u ON ((s.student_id = u.user_id)))
     JOIN user_personal_info upi ON ((u.user_id = upi.user_id)))
     LEFT JOIN student_accounts sa ON ((s.student_id = sa.student_id)));

CREATE VIEW v_user_complete_profile AS
SELECT
    NULL::uuid AS user_id,
    NULL::character varying(50) AS username,
    NULL::character varying(255) AS email,
    NULL::boolean AS is_active,
    NULL::character varying(100) AS first_name,
    NULL::character varying(100) AS last_name,
    NULL::character varying(100) AS middle_name,
    NULL::character varying(100) AS preferred_name,
    NULL::date AS date_of_birth,
    NULL::character varying(20) AS gender,
    NULL::character varying(100) AS nationality,
    NULL::character varying[] AS roles,
    NULL::timestamp without time zone AS last_login,
    NULL::timestamp without time zone AS created_at;

CREATE TABLE withdrawal_requests (
    request_id integer NOT NULL,
    enrollment_id integer NOT NULL,
    student_id uuid NOT NULL,
    reason text NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    reviewed_by uuid,
    reviewed_at timestamp without time zone,
    reviewer_note text,
    created_at timestamp without time zone DEFAULT now()
);

CREATE SEQUENCE withdrawal_requests_request_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE withdrawal_requests_request_id_seq OWNED BY withdrawal_requests.request_id;

ALTER TABLE ONLY academic_terms ALTER COLUMN term_id SET DEFAULT nextval('academic_terms_term_id_seq'::regclass);

ALTER TABLE ONLY announcements ALTER COLUMN announcement_id SET DEFAULT nextval('announcements_announcement_id_seq'::regclass);

ALTER TABLE ONLY assignment_submissions ALTER COLUMN submission_id SET DEFAULT nextval('assignment_submissions_submission_id_seq'::regclass);

ALTER TABLE ONLY assignments ALTER COLUMN assignment_id SET DEFAULT nextval('assignments_assignment_id_seq'::regclass);

ALTER TABLE ONLY attendance ALTER COLUMN attendance_id SET DEFAULT nextval('attendance_attendance_id_seq'::regclass);

ALTER TABLE ONLY audit_logs ALTER COLUMN log_id SET DEFAULT nextval('audit_logs_log_id_seq'::regclass);

ALTER TABLE ONLY buildings ALTER COLUMN building_id SET DEFAULT nextval('buildings_building_id_seq'::regclass);

ALTER TABLE ONLY course_corequisites ALTER COLUMN corequisite_id SET DEFAULT nextval('course_corequisites_corequisite_id_seq'::regclass);

ALTER TABLE ONLY course_prerequisites ALTER COLUMN prerequisite_id SET DEFAULT nextval('course_prerequisites_prerequisite_id_seq'::regclass);

ALTER TABLE ONLY course_sections ALTER COLUMN section_id SET DEFAULT nextval('course_sections_section_id_seq'::regclass);

ALTER TABLE ONLY courses ALTER COLUMN course_id SET DEFAULT nextval('courses_course_id_seq'::regclass);

ALTER TABLE ONLY departments ALTER COLUMN department_id SET DEFAULT nextval('departments_department_id_seq'::regclass);

ALTER TABLE ONLY enrollments ALTER COLUMN enrollment_id SET DEFAULT nextval('enrollments_enrollment_id_seq'::regclass);

ALTER TABLE ONLY event_registrations ALTER COLUMN registration_id SET DEFAULT nextval('event_registrations_registration_id_seq'::regclass);

ALTER TABLE ONLY events ALTER COLUMN event_id SET DEFAULT nextval('events_event_id_seq'::regclass);

ALTER TABLE ONLY faculty_publications ALTER COLUMN faculty_publication_id SET DEFAULT nextval('faculty_publications_faculty_publication_id_seq'::regclass);

ALTER TABLE ONLY fee_structures ALTER COLUMN fee_structure_id SET DEFAULT nextval('fee_structures_fee_structure_id_seq'::regclass);

ALTER TABLE ONLY fee_types ALTER COLUMN fee_type_id SET DEFAULT nextval('fee_types_fee_type_id_seq'::regclass);

ALTER TABLE ONLY financial_transactions ALTER COLUMN transaction_id SET DEFAULT nextval('financial_transactions_transaction_id_seq'::regclass);

ALTER TABLE ONLY grade_scale_items ALTER COLUMN item_id SET DEFAULT nextval('grade_scale_items_item_id_seq'::regclass);

ALTER TABLE ONLY grade_scales ALTER COLUMN scale_id SET DEFAULT nextval('grade_scales_scale_id_seq'::regclass);

ALTER TABLE ONLY library_checkouts ALTER COLUMN checkout_id SET DEFAULT nextval('library_checkouts_checkout_id_seq'::regclass);

ALTER TABLE ONLY library_items ALTER COLUMN item_id SET DEFAULT nextval('library_items_item_id_seq'::regclass);

ALTER TABLE ONLY library_reservations ALTER COLUMN reservation_id SET DEFAULT nextval('library_reservations_reservation_id_seq'::regclass);

ALTER TABLE ONLY notifications ALTER COLUMN notification_id SET DEFAULT nextval('notifications_notification_id_seq'::regclass);

ALTER TABLE ONLY organization_members ALTER COLUMN membership_id SET DEFAULT nextval('organization_members_membership_id_seq'::regclass);

ALTER TABLE ONLY organizations ALTER COLUMN organization_id SET DEFAULT nextval('organizations_organization_id_seq'::regclass);

ALTER TABLE ONLY programs ALTER COLUMN program_id SET DEFAULT nextval('programs_program_id_seq'::regclass);

ALTER TABLE ONLY publications ALTER COLUMN publication_id SET DEFAULT nextval('publications_publication_id_seq'::regclass);

ALTER TABLE ONLY research_projects ALTER COLUMN project_id SET DEFAULT nextval('research_projects_project_id_seq'::regclass);

ALTER TABLE ONLY research_team_members ALTER COLUMN member_id SET DEFAULT nextval('research_team_members_member_id_seq'::regclass);

ALTER TABLE ONLY reviews ALTER COLUMN review_id SET DEFAULT nextval('reviews_review_id_seq'::regclass);

ALTER TABLE ONLY rooms ALTER COLUMN room_id SET DEFAULT nextval('rooms_room_id_seq'::regclass);

ALTER TABLE ONLY scholarship_awards ALTER COLUMN award_id SET DEFAULT nextval('scholarship_awards_award_id_seq'::regclass);

ALTER TABLE ONLY scholarships ALTER COLUMN scholarship_id SET DEFAULT nextval('scholarships_scholarship_id_seq'::regclass);

ALTER TABLE ONLY student_accounts ALTER COLUMN account_id SET DEFAULT nextval('student_accounts_account_id_seq'::regclass);

ALTER TABLE ONLY system_settings ALTER COLUMN setting_id SET DEFAULT nextval('system_settings_setting_id_seq'::regclass);

ALTER TABLE ONLY user_addresses ALTER COLUMN address_id SET DEFAULT nextval('user_addresses_address_id_seq'::regclass);

ALTER TABLE ONLY user_contact_info ALTER COLUMN contact_id SET DEFAULT nextval('user_contact_info_contact_id_seq'::regclass);

ALTER TABLE ONLY user_emergency_contacts ALTER COLUMN emergency_contact_id SET DEFAULT nextval('user_emergency_contacts_emergency_contact_id_seq'::regclass);

ALTER TABLE ONLY user_personal_info ALTER COLUMN info_id SET DEFAULT nextval('user_personal_info_info_id_seq'::regclass);

ALTER TABLE ONLY user_preferences ALTER COLUMN preference_id SET DEFAULT nextval('user_preferences_preference_id_seq'::regclass);

ALTER TABLE ONLY user_role_assignments ALTER COLUMN assignment_id SET DEFAULT nextval('user_role_assignments_assignment_id_seq'::regclass);

ALTER TABLE ONLY user_roles ALTER COLUMN role_id SET DEFAULT nextval('user_roles_role_id_seq'::regclass);

ALTER TABLE ONLY withdrawal_requests ALTER COLUMN request_id SET DEFAULT nextval('withdrawal_requests_request_id_seq'::regclass);

ALTER TABLE ONLY academic_terms
    ADD CONSTRAINT academic_terms_pkey PRIMARY KEY (term_id);

ALTER TABLE ONLY academic_terms
    ADD CONSTRAINT academic_terms_term_code_key UNIQUE (term_code);

ALTER TABLE ONLY alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);

ALTER TABLE ONLY announcements
    ADD CONSTRAINT announcements_pkey PRIMARY KEY (announcement_id);

ALTER TABLE ONLY assignment_submissions
    ADD CONSTRAINT assignment_submissions_pkey PRIMARY KEY (submission_id);

ALTER TABLE ONLY assignments
    ADD CONSTRAINT assignments_pkey PRIMARY KEY (assignment_id);

ALTER TABLE ONLY attendance
    ADD CONSTRAINT attendance_pkey PRIMARY KEY (attendance_id);

ALTER TABLE ONLY audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (log_id);

ALTER TABLE ONLY buildings
    ADD CONSTRAINT buildings_building_code_key UNIQUE (building_code);

ALTER TABLE ONLY buildings
    ADD CONSTRAINT buildings_pkey PRIMARY KEY (building_id);

ALTER TABLE ONLY course_corequisites
    ADD CONSTRAINT course_corequisites_pkey PRIMARY KEY (corequisite_id);

ALTER TABLE ONLY course_prerequisites
    ADD CONSTRAINT course_prerequisites_pkey PRIMARY KEY (prerequisite_id);

ALTER TABLE ONLY course_sections
    ADD CONSTRAINT course_sections_pkey PRIMARY KEY (section_id);

ALTER TABLE ONLY courses
    ADD CONSTRAINT courses_course_code_key UNIQUE (course_code);

ALTER TABLE ONLY courses
    ADD CONSTRAINT courses_pkey PRIMARY KEY (course_id);

ALTER TABLE ONLY departments
    ADD CONSTRAINT departments_department_code_key UNIQUE (department_code);

ALTER TABLE ONLY departments
    ADD CONSTRAINT departments_department_name_key UNIQUE (department_name);

ALTER TABLE ONLY departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (department_id);

ALTER TABLE ONLY enrollments
    ADD CONSTRAINT enrollments_pkey PRIMARY KEY (enrollment_id);

ALTER TABLE ONLY event_registrations
    ADD CONSTRAINT event_registrations_pkey PRIMARY KEY (registration_id);

ALTER TABLE ONLY events
    ADD CONSTRAINT events_event_code_key UNIQUE (event_code);

ALTER TABLE ONLY events
    ADD CONSTRAINT events_pkey PRIMARY KEY (event_id);

ALTER TABLE ONLY faculty
    ADD CONSTRAINT faculty_employee_number_key UNIQUE (employee_number);

ALTER TABLE ONLY faculty
    ADD CONSTRAINT faculty_pkey PRIMARY KEY (faculty_id);

ALTER TABLE ONLY faculty_publications
    ADD CONSTRAINT faculty_publications_pkey PRIMARY KEY (faculty_publication_id);

ALTER TABLE ONLY fee_structures
    ADD CONSTRAINT fee_structures_pkey PRIMARY KEY (fee_structure_id);

ALTER TABLE ONLY fee_types
    ADD CONSTRAINT fee_types_fee_type_code_key UNIQUE (fee_type_code);

ALTER TABLE ONLY fee_types
    ADD CONSTRAINT fee_types_pkey PRIMARY KEY (fee_type_id);

ALTER TABLE ONLY financial_transactions
    ADD CONSTRAINT financial_transactions_pkey PRIMARY KEY (transaction_id);

ALTER TABLE ONLY grade_scale_items
    ADD CONSTRAINT grade_scale_items_pkey PRIMARY KEY (item_id);

ALTER TABLE ONLY grade_scales
    ADD CONSTRAINT grade_scales_pkey PRIMARY KEY (scale_id);

ALTER TABLE ONLY library_checkouts
    ADD CONSTRAINT library_checkouts_pkey PRIMARY KEY (checkout_id);

ALTER TABLE ONLY library_items
    ADD CONSTRAINT library_items_pkey PRIMARY KEY (item_id);

ALTER TABLE ONLY library_reservations
    ADD CONSTRAINT library_reservations_pkey PRIMARY KEY (reservation_id);

ALTER TABLE ONLY notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (notification_id);

ALTER TABLE ONLY organization_members
    ADD CONSTRAINT organization_members_pkey PRIMARY KEY (membership_id);

ALTER TABLE ONLY organizations
    ADD CONSTRAINT organizations_organization_code_key UNIQUE (organization_code);

ALTER TABLE ONLY organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (organization_id);

ALTER TABLE ONLY programs
    ADD CONSTRAINT programs_pkey PRIMARY KEY (program_id);

ALTER TABLE ONLY programs
    ADD CONSTRAINT programs_program_code_key UNIQUE (program_code);

ALTER TABLE ONLY publications
    ADD CONSTRAINT publications_pkey PRIMARY KEY (publication_id);

ALTER TABLE ONLY research_projects
    ADD CONSTRAINT research_projects_pkey PRIMARY KEY (project_id);

ALTER TABLE ONLY research_projects
    ADD CONSTRAINT research_projects_project_code_key UNIQUE (project_code);

ALTER TABLE ONLY research_team_members
    ADD CONSTRAINT research_team_members_pkey PRIMARY KEY (member_id);

ALTER TABLE ONLY reviews
    ADD CONSTRAINT reviews_pkey PRIMARY KEY (review_id);

ALTER TABLE ONLY rooms
    ADD CONSTRAINT rooms_pkey PRIMARY KEY (room_id);

ALTER TABLE ONLY scholarship_awards
    ADD CONSTRAINT scholarship_awards_pkey PRIMARY KEY (award_id);

ALTER TABLE ONLY scholarships
    ADD CONSTRAINT scholarships_pkey PRIMARY KEY (scholarship_id);

ALTER TABLE ONLY scholarships
    ADD CONSTRAINT scholarships_scholarship_code_key UNIQUE (scholarship_code);

ALTER TABLE ONLY staff
    ADD CONSTRAINT staff_employee_number_key UNIQUE (employee_number);

ALTER TABLE ONLY staff
    ADD CONSTRAINT staff_pkey PRIMARY KEY (staff_id);

ALTER TABLE ONLY student_accounts
    ADD CONSTRAINT student_accounts_account_number_key UNIQUE (account_number);

ALTER TABLE ONLY student_accounts
    ADD CONSTRAINT student_accounts_pkey PRIMARY KEY (account_id);

ALTER TABLE ONLY student_accounts
    ADD CONSTRAINT student_accounts_student_id_key UNIQUE (student_id);

ALTER TABLE ONLY students
    ADD CONSTRAINT students_pkey PRIMARY KEY (student_id);

ALTER TABLE ONLY students
    ADD CONSTRAINT students_student_number_key UNIQUE (student_number);

ALTER TABLE ONLY system_settings
    ADD CONSTRAINT system_settings_pkey PRIMARY KEY (setting_id);

ALTER TABLE ONLY system_settings
    ADD CONSTRAINT system_settings_setting_key_key UNIQUE (setting_key);

ALTER TABLE ONLY library_reservations
    ADD CONSTRAINT uq_active_reservation UNIQUE (item_id, user_id, reservation_status);

ALTER TABLE ONLY assignment_submissions
    ADD CONSTRAINT uq_assignment_student UNIQUE (assignment_id, student_id);

ALTER TABLE ONLY rooms
    ADD CONSTRAINT uq_building_room UNIQUE (building_id, room_number);

ALTER TABLE ONLY user_contact_info
    ADD CONSTRAINT uq_contact UNIQUE (user_id, contact_type, contact_value);

ALTER TABLE ONLY course_corequisites
    ADD CONSTRAINT uq_course_corequisite UNIQUE (course_id, corequisite_course_id);

ALTER TABLE ONLY course_prerequisites
    ADD CONSTRAINT uq_course_prerequisite UNIQUE (course_id, prerequisite_course_id);

ALTER TABLE ONLY course_sections
    ADD CONSTRAINT uq_course_term_section UNIQUE (course_id, term_id, section_number);

ALTER TABLE ONLY event_registrations
    ADD CONSTRAINT uq_event_user UNIQUE (event_id, user_id);

ALTER TABLE ONLY faculty_publications
    ADD CONSTRAINT uq_faculty_publication UNIQUE (faculty_id, publication_id);

ALTER TABLE ONLY organization_members
    ADD CONSTRAINT uq_org_student UNIQUE (organization_id, student_id);

ALTER TABLE ONLY research_team_members
    ADD CONSTRAINT uq_project_user UNIQUE (project_id, user_id);

ALTER TABLE ONLY reviews
    ADD CONSTRAINT uq_review_enrollment UNIQUE (enrollment_id);

ALTER TABLE ONLY attendance
    ADD CONSTRAINT uq_section_student_date UNIQUE (section_id, student_id, class_date);

ALTER TABLE ONLY enrollments
    ADD CONSTRAINT uq_student_section UNIQUE (student_id, section_id);

ALTER TABLE ONLY user_role_assignments
    ADD CONSTRAINT uq_user_role UNIQUE (user_id, role_id);

ALTER TABLE ONLY user_addresses
    ADD CONSTRAINT user_addresses_pkey PRIMARY KEY (address_id);

ALTER TABLE ONLY user_contact_info
    ADD CONSTRAINT user_contact_info_pkey PRIMARY KEY (contact_id);

ALTER TABLE ONLY user_emergency_contacts
    ADD CONSTRAINT user_emergency_contacts_pkey PRIMARY KEY (emergency_contact_id);

ALTER TABLE ONLY user_personal_info
    ADD CONSTRAINT user_personal_info_pkey PRIMARY KEY (info_id);

ALTER TABLE ONLY user_personal_info
    ADD CONSTRAINT user_personal_info_user_id_key UNIQUE (user_id);

ALTER TABLE ONLY user_preferences
    ADD CONSTRAINT user_preferences_pkey PRIMARY KEY (preference_id);

ALTER TABLE ONLY user_preferences
    ADD CONSTRAINT user_preferences_user_id_key UNIQUE (user_id);

ALTER TABLE ONLY user_role_assignments
    ADD CONSTRAINT user_role_assignments_pkey PRIMARY KEY (assignment_id);

ALTER TABLE ONLY user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (role_id);

ALTER TABLE ONLY user_roles
    ADD CONSTRAINT user_roles_role_name_key UNIQUE (role_name);

ALTER TABLE ONLY user_sessions
    ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (session_id);

ALTER TABLE ONLY users
    ADD CONSTRAINT users_email_key UNIQUE (email);

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);

ALTER TABLE ONLY users
    ADD CONSTRAINT users_username_key UNIQUE (username);

ALTER TABLE ONLY withdrawal_requests
    ADD CONSTRAINT withdrawal_requests_pkey PRIMARY KEY (request_id);

CREATE INDEX idx_account_balance ON student_accounts USING btree (balance);

CREATE INDEX idx_account_hold ON student_accounts USING btree (has_hold);

CREATE INDEX idx_account_student ON student_accounts USING btree (student_id);

CREATE INDEX idx_announce_active ON announcements USING btree (is_active);

CREATE INDEX idx_announce_audience ON announcements USING btree (target_audience);

CREATE INDEX idx_announce_dates ON announcements USING btree (start_datetime, end_datetime);

CREATE INDEX idx_assign_due_date ON assignments USING btree (due_date);

CREATE INDEX idx_assign_section ON assignments USING btree (section_id);

CREATE INDEX idx_assign_type ON assignments USING btree (assignment_type);

CREATE INDEX idx_attend_date ON attendance USING btree (class_date);

CREATE INDEX idx_attend_section ON attendance USING btree (section_id);

CREATE INDEX idx_attend_student ON attendance USING btree (student_id);

CREATE INDEX idx_audit_action ON audit_logs USING btree (action);

CREATE INDEX idx_audit_created ON audit_logs USING btree (created_at);

CREATE INDEX idx_audit_entity ON audit_logs USING btree (entity_type, entity_id);

CREATE INDEX idx_audit_user ON audit_logs USING btree (user_id);

CREATE INDEX idx_award_scholarship ON scholarship_awards USING btree (scholarship_id);

CREATE INDEX idx_award_status ON scholarship_awards USING btree (award_status);

CREATE INDEX idx_award_student ON scholarship_awards USING btree (student_id);

CREATE INDEX idx_award_term ON scholarship_awards USING btree (term_id);

CREATE INDEX idx_building_active ON buildings USING btree (is_active);

CREATE INDEX idx_building_code ON buildings USING btree (building_code);

CREATE INDEX idx_checkout_due ON library_checkouts USING btree (due_date);

CREATE INDEX idx_checkout_item ON library_checkouts USING btree (item_id);

CREATE INDEX idx_checkout_status ON library_checkouts USING btree (checkout_status);

CREATE INDEX idx_checkout_user ON library_checkouts USING btree (user_id);

CREATE INDEX idx_coreq_course ON course_corequisites USING btree (course_id);

CREATE INDEX idx_course_active ON courses USING btree (is_active);

CREATE INDEX idx_course_code ON courses USING btree (course_code);

CREATE INDEX idx_course_dept ON courses USING btree (department_id);

CREATE INDEX idx_course_level ON courses USING btree (course_level);

CREATE INDEX idx_course_sections_term_status ON course_sections USING btree (term_id, status);

CREATE INDEX idx_dept_active ON departments USING btree (is_active);

CREATE INDEX idx_dept_code ON departments USING btree (department_code);

CREATE INDEX idx_dept_head ON departments USING btree (head_faculty_id);

CREATE INDEX idx_enroll_grade ON enrollments USING btree (grade);

CREATE INDEX idx_enroll_section ON enrollments USING btree (section_id);

CREATE INDEX idx_enroll_status ON enrollments USING btree (enrollment_status);

CREATE INDEX idx_enroll_student ON enrollments USING btree (student_id);

CREATE INDEX idx_enrollments_section_status ON enrollments USING btree (section_id, enrollment_status);

CREATE INDEX idx_enrollments_student_status ON enrollments USING btree (student_id, enrollment_status);

CREATE INDEX idx_ereg_attendance ON event_registrations USING btree (attendance_status);

CREATE INDEX idx_ereg_event ON event_registrations USING btree (event_id);

CREATE INDEX idx_ereg_user ON event_registrations USING btree (user_id);

CREATE INDEX idx_event_dates ON events USING btree (start_datetime, end_datetime);

CREATE INDEX idx_event_organizer ON events USING btree (organizer_id);

CREATE INDEX idx_event_status ON events USING btree (event_status);

CREATE INDEX idx_event_type ON events USING btree (event_type);

CREATE INDEX idx_faculty_active ON faculty USING btree (faculty_id) WHERE ((employment_status)::text = 'active'::text);

CREATE INDEX idx_faculty_dept ON faculty USING btree (department_id);

CREATE INDEX idx_faculty_employee_number ON faculty USING btree (employee_number);

CREATE INDEX idx_faculty_rank ON faculty USING btree (faculty_rank);

CREATE INDEX idx_faculty_status ON faculty USING btree (employment_status);

CREATE INDEX idx_fee_struct_program ON fee_structures USING btree (program_id);

CREATE INDEX idx_fee_struct_term ON fee_structures USING btree (term_id);

CREATE INDEX idx_fee_struct_type ON fee_structures USING btree (fee_type_id);

CREATE INDEX idx_fee_type_code ON fee_types USING btree (fee_type_code);

CREATE INDEX idx_financial_trans_account_type ON financial_transactions USING btree (account_id, transaction_type);

CREATE INDEX idx_fpub_faculty ON faculty_publications USING btree (faculty_id);

CREATE INDEX idx_fpub_publication ON faculty_publications USING btree (publication_id);

CREATE INDEX idx_lib_author ON library_items USING btree (author);

CREATE INDEX idx_lib_call_number ON library_items USING btree (call_number);

CREATE INDEX idx_lib_isbn ON library_items USING btree (isbn);

CREATE INDEX idx_lib_status ON library_items USING btree (item_status);

CREATE INDEX idx_lib_title ON library_items USING btree (title);

CREATE INDEX idx_lib_type ON library_items USING btree (item_type);

CREATE INDEX idx_member_org ON organization_members USING btree (organization_id);

CREATE INDEX idx_member_status ON organization_members USING btree (membership_status);

CREATE INDEX idx_member_student ON organization_members USING btree (student_id);

CREATE INDEX idx_notif_created ON notifications USING btree (created_at);

CREATE INDEX idx_notif_read ON notifications USING btree (is_read);

CREATE INDEX idx_notif_type ON notifications USING btree (notification_type);

CREATE INDEX idx_notif_user ON notifications USING btree (user_id);

CREATE INDEX idx_org_active ON organizations USING btree (is_active);

CREATE INDEX idx_org_advisor ON organizations USING btree (advisor_id);

CREATE INDEX idx_org_code ON organizations USING btree (organization_code);

CREATE INDEX idx_org_type ON organizations USING btree (organization_type);

CREATE INDEX idx_prereq_course ON course_prerequisites USING btree (course_id);

CREATE INDEX idx_prereq_prerequisite ON course_prerequisites USING btree (prerequisite_course_id);

CREATE INDEX idx_prog_active ON programs USING btree (is_active);

CREATE INDEX idx_prog_code ON programs USING btree (program_code);

CREATE INDEX idx_prog_dept ON programs USING btree (department_id);

CREATE INDEX idx_prog_level ON programs USING btree (degree_level);

CREATE INDEX idx_project_code ON research_projects USING btree (project_code);

CREATE INDEX idx_project_dept ON research_projects USING btree (department_id);

CREATE INDEX idx_project_pi ON research_projects USING btree (principal_investigator_id);

CREATE INDEX idx_project_status ON research_projects USING btree (project_status);

CREATE INDEX idx_pub_date ON publications USING btree (publication_date);

CREATE INDEX idx_pub_doi ON publications USING btree (doi);

CREATE INDEX idx_pub_project ON publications USING btree (project_id);

CREATE INDEX idx_pub_type ON publications USING btree (publication_type);

CREATE INDEX idx_reserve_item ON library_reservations USING btree (item_id);

CREATE INDEX idx_reserve_status ON library_reservations USING btree (reservation_status);

CREATE INDEX idx_reserve_user ON library_reservations USING btree (user_id);

CREATE INDEX idx_room_active ON rooms USING btree (is_active);

CREATE INDEX idx_room_building ON rooms USING btree (building_id);

CREATE INDEX idx_room_capacity ON rooms USING btree (capacity);

CREATE INDEX idx_room_type ON rooms USING btree (room_type);

CREATE INDEX idx_scholarship_active ON scholarships USING btree (is_active);

CREATE INDEX idx_scholarship_code ON scholarships USING btree (scholarship_code);

CREATE INDEX idx_scholarship_type ON scholarships USING btree (scholarship_type);

CREATE INDEX idx_section_course ON course_sections USING btree (course_id);

CREATE INDEX idx_section_instructor ON course_sections USING btree (instructor_id);

CREATE INDEX idx_section_room ON course_sections USING btree (room_id);

CREATE INDEX idx_section_status ON course_sections USING btree (status);

CREATE INDEX idx_section_term ON course_sections USING btree (term_id);

CREATE INDEX idx_sections_open ON course_sections USING btree (section_id) WHERE ((status)::text = 'open'::text);

CREATE INDEX idx_session_active ON user_sessions USING btree (is_active);

CREATE INDEX idx_session_expires ON user_sessions USING btree (expires_at);

CREATE INDEX idx_session_user ON user_sessions USING btree (user_id);

CREATE INDEX idx_setting_key ON system_settings USING btree (setting_key);

CREATE INDEX idx_staff_dept ON staff USING btree (department_id);

CREATE INDEX idx_staff_employee_number ON staff USING btree (employee_number);

CREATE INDEX idx_staff_status ON staff USING btree (employment_status);

CREATE INDEX idx_staff_supervisor ON staff USING btree (supervisor_id);

CREATE INDEX idx_student_advisor ON students USING btree (advisor_id);

CREATE INDEX idx_student_number ON students USING btree (student_number);

CREATE INDEX idx_student_program ON students USING btree (program_id);

CREATE INDEX idx_student_standing ON students USING btree (academic_standing);

CREATE INDEX idx_student_status ON students USING btree (enrollment_status);

CREATE INDEX idx_students_active ON students USING btree (student_id) WHERE ((enrollment_status)::text = 'active'::text);

CREATE INDEX idx_students_program_status ON students USING btree (program_id, enrollment_status);

CREATE INDEX idx_sub_assignment ON assignment_submissions USING btree (assignment_id);

CREATE INDEX idx_sub_status ON assignment_submissions USING btree (submission_status);

CREATE INDEX idx_sub_student ON assignment_submissions USING btree (student_id);

CREATE INDEX idx_team_project ON research_team_members USING btree (project_id);

CREATE INDEX idx_team_user ON research_team_members USING btree (user_id);

CREATE INDEX idx_term_code ON academic_terms USING btree (term_code);

CREATE INDEX idx_term_dates ON academic_terms USING btree (start_date, end_date);

CREATE INDEX idx_term_status ON academic_terms USING btree (status);

CREATE INDEX idx_term_year ON academic_terms USING btree (academic_year);

CREATE INDEX idx_trans_account ON financial_transactions USING btree (account_id);

CREATE INDEX idx_trans_date ON financial_transactions USING btree (transaction_date);

CREATE INDEX idx_trans_reference ON financial_transactions USING btree (reference_number);

CREATE INDEX idx_trans_term ON financial_transactions USING btree (term_id);

CREATE INDEX idx_trans_type ON financial_transactions USING btree (transaction_type);

CREATE INDEX idx_ua_city ON user_addresses USING btree (city);

CREATE INDEX idx_ua_primary ON user_addresses USING btree (user_id, is_primary);

CREATE INDEX idx_ua_user ON user_addresses USING btree (user_id);

CREATE INDEX idx_uci_primary ON user_contact_info USING btree (user_id, is_primary);

CREATE INDEX idx_uci_user ON user_contact_info USING btree (user_id);

CREATE INDEX idx_uec_user ON user_emergency_contacts USING btree (user_id);

CREATE INDEX idx_up_user ON user_preferences USING btree (user_id);

CREATE INDEX idx_upi_last_name ON user_personal_info USING btree (last_name);

CREATE INDEX idx_upi_user ON user_personal_info USING btree (user_id);

CREATE INDEX idx_ura_active ON user_role_assignments USING btree (is_active);

CREATE INDEX idx_ura_role ON user_role_assignments USING btree (role_id);

CREATE INDEX idx_ura_user ON user_role_assignments USING btree (user_id);

CREATE INDEX idx_user_roles_name ON user_roles USING btree (role_name);

CREATE INDEX idx_users_active ON users USING btree (is_active);

CREATE INDEX idx_users_active_email ON users USING btree (email) WHERE (is_active = true);

CREATE INDEX idx_users_email ON users USING btree (email);

CREATE INDEX idx_users_username ON users USING btree (username);

CREATE OR REPLACE VIEW v_user_complete_profile AS
 SELECT u.user_id,
    u.username,
    u.email,
    u.is_active,
    upi.first_name,
    upi.last_name,
    upi.middle_name,
    upi.preferred_name,
    upi.date_of_birth,
    upi.gender,
    upi.nationality,
    array_agg(DISTINCT r.role_name) FILTER (WHERE (r.role_name IS NOT NULL)) AS roles,
    u.last_login,
    u.created_at
   FROM (((users u
     LEFT JOIN user_personal_info upi ON ((u.user_id = upi.user_id)))
     LEFT JOIN user_role_assignments ura ON (((u.user_id = ura.user_id) AND (ura.is_active = true))))
     LEFT JOIN user_roles r ON ((ura.role_id = r.role_id)))
  GROUP BY u.user_id, upi.first_name, upi.last_name, upi.middle_name, upi.preferred_name, upi.date_of_birth, upi.gender, upi.nationality;

CREATE TRIGGER trg_audit_users AFTER INSERT OR DELETE OR UPDATE ON users FOR EACH ROW EXECUTE FUNCTION log_user_activity();

CREATE TRIGGER trg_courses_updated_at BEFORE UPDATE ON courses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_departments_updated_at BEFORE UPDATE ON departments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_enrollments_updated_at BEFORE UPDATE ON enrollments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_faculty_updated_at BEFORE UPDATE ON faculty FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_programs_updated_at BEFORE UPDATE ON programs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_staff_updated_at BEFORE UPDATE ON staff FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_students_updated_at BEFORE UPDATE ON students FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_update_account_balance AFTER INSERT ON financial_transactions FOR EACH ROW EXECUTE FUNCTION update_student_account_balance();

CREATE TRIGGER trg_update_enrollment_count AFTER INSERT OR DELETE OR UPDATE ON enrollments FOR EACH ROW EXECUTE FUNCTION update_section_enrollment_count();

CREATE TRIGGER trg_update_library_availability AFTER INSERT OR UPDATE ON library_checkouts FOR EACH ROW EXECUTE FUNCTION update_library_availability();

CREATE TRIGGER trg_user_addresses_updated_at BEFORE UPDATE ON user_addresses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_user_contact_info_updated_at BEFORE UPDATE ON user_contact_info FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_user_personal_info_updated_at BEFORE UPDATE ON user_personal_info FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

ALTER TABLE ONLY student_accounts
    ADD CONSTRAINT fk_account_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE;

ALTER TABLE ONLY announcements
    ADD CONSTRAINT fk_announce_dept FOREIGN KEY (department_id) REFERENCES departments(department_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY announcements
    ADD CONSTRAINT fk_announce_posted_by FOREIGN KEY (posted_by) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY announcements
    ADD CONSTRAINT fk_announce_program FOREIGN KEY (program_id) REFERENCES programs(program_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY assignments
    ADD CONSTRAINT fk_assign_created_by FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE ONLY assignments
    ADD CONSTRAINT fk_assign_section FOREIGN KEY (section_id) REFERENCES course_sections(section_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY attendance
    ADD CONSTRAINT fk_attend_recorded_by FOREIGN KEY (recorded_by) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE ONLY attendance
    ADD CONSTRAINT fk_attend_section FOREIGN KEY (section_id) REFERENCES course_sections(section_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY attendance
    ADD CONSTRAINT fk_attend_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY audit_logs
    ADD CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY scholarship_awards
    ADD CONSTRAINT fk_award_approved_by FOREIGN KEY (approved_by) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY scholarship_awards
    ADD CONSTRAINT fk_award_scholarship FOREIGN KEY (scholarship_id) REFERENCES scholarships(scholarship_id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY scholarship_awards
    ADD CONSTRAINT fk_award_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY scholarship_awards
    ADD CONSTRAINT fk_award_term FOREIGN KEY (term_id) REFERENCES academic_terms(term_id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY library_checkouts
    ADD CONSTRAINT fk_checkin_by FOREIGN KEY (checked_in_by) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY library_checkouts
    ADD CONSTRAINT fk_checkout_by FOREIGN KEY (checked_out_by) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY library_checkouts
    ADD CONSTRAINT fk_checkout_item FOREIGN KEY (item_id) REFERENCES library_items(item_id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY library_checkouts
    ADD CONSTRAINT fk_checkout_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY course_corequisites
    ADD CONSTRAINT fk_coreq_corequisite FOREIGN KEY (corequisite_course_id) REFERENCES courses(course_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY course_corequisites
    ADD CONSTRAINT fk_coreq_course FOREIGN KEY (course_id) REFERENCES courses(course_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY courses
    ADD CONSTRAINT fk_course_dept FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE CASCADE;

ALTER TABLE ONLY departments
    ADD CONSTRAINT fk_dept_head FOREIGN KEY (head_faculty_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY departments
    ADD CONSTRAINT fk_dept_parent FOREIGN KEY (parent_department_id) REFERENCES departments(department_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY enrollments
    ADD CONSTRAINT fk_enroll_graded_by FOREIGN KEY (grade_submitted_by) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY enrollments
    ADD CONSTRAINT fk_enroll_section FOREIGN KEY (section_id) REFERENCES course_sections(section_id) ON DELETE CASCADE;

ALTER TABLE ONLY enrollments
    ADD CONSTRAINT fk_enroll_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE;

ALTER TABLE ONLY event_registrations
    ADD CONSTRAINT fk_ereg_event FOREIGN KEY (event_id) REFERENCES events(event_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY event_registrations
    ADD CONSTRAINT fk_ereg_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY events
    ADD CONSTRAINT fk_event_dept FOREIGN KEY (department_id) REFERENCES departments(department_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY events
    ADD CONSTRAINT fk_event_organizer FOREIGN KEY (organizer_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY events
    ADD CONSTRAINT fk_event_room FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY faculty
    ADD CONSTRAINT fk_faculty_dept FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE CASCADE;

ALTER TABLE ONLY faculty
    ADD CONSTRAINT fk_faculty_office FOREIGN KEY (office_room_id) REFERENCES rooms(room_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY faculty
    ADD CONSTRAINT fk_faculty_user FOREIGN KEY (faculty_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY fee_structures
    ADD CONSTRAINT fk_fee_program FOREIGN KEY (program_id) REFERENCES programs(program_id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY fee_structures
    ADD CONSTRAINT fk_fee_term FOREIGN KEY (term_id) REFERENCES academic_terms(term_id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY fee_structures
    ADD CONSTRAINT fk_fee_type FOREIGN KEY (fee_type_id) REFERENCES fee_types(fee_type_id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY faculty_publications
    ADD CONSTRAINT fk_fpub_faculty FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY faculty_publications
    ADD CONSTRAINT fk_fpub_publication FOREIGN KEY (publication_id) REFERENCES publications(publication_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY grade_scale_items
    ADD CONSTRAINT fk_gsi_scale FOREIGN KEY (scale_id) REFERENCES grade_scales(scale_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY organization_members
    ADD CONSTRAINT fk_member_org FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY organization_members
    ADD CONSTRAINT fk_member_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY notifications
    ADD CONSTRAINT fk_notif_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY organizations
    ADD CONSTRAINT fk_org_advisor FOREIGN KEY (advisor_id) REFERENCES faculty(faculty_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY organizations
    ADD CONSTRAINT fk_org_dept FOREIGN KEY (department_id) REFERENCES departments(department_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY organizations
    ADD CONSTRAINT fk_org_president FOREIGN KEY (president_id) REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY course_prerequisites
    ADD CONSTRAINT fk_prereq_course FOREIGN KEY (course_id) REFERENCES courses(course_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY course_prerequisites
    ADD CONSTRAINT fk_prereq_prerequisite FOREIGN KEY (prerequisite_course_id) REFERENCES courses(course_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY programs
    ADD CONSTRAINT fk_prog_coordinator FOREIGN KEY (coordinator_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY programs
    ADD CONSTRAINT fk_prog_dept FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE CASCADE;

ALTER TABLE ONLY research_projects
    ADD CONSTRAINT fk_project_dept FOREIGN KEY (department_id) REFERENCES departments(department_id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY research_projects
    ADD CONSTRAINT fk_project_pi FOREIGN KEY (principal_investigator_id) REFERENCES faculty(faculty_id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY publications
    ADD CONSTRAINT fk_pub_project FOREIGN KEY (project_id) REFERENCES research_projects(project_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY library_reservations
    ADD CONSTRAINT fk_reserve_item FOREIGN KEY (item_id) REFERENCES library_items(item_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY library_reservations
    ADD CONSTRAINT fk_reserve_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY rooms
    ADD CONSTRAINT fk_room_building FOREIGN KEY (building_id) REFERENCES buildings(building_id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY course_sections
    ADD CONSTRAINT fk_section_course FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE;

ALTER TABLE ONLY course_sections
    ADD CONSTRAINT fk_section_instructor FOREIGN KEY (instructor_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY course_sections
    ADD CONSTRAINT fk_section_room FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY course_sections
    ADD CONSTRAINT fk_section_term FOREIGN KEY (term_id) REFERENCES academic_terms(term_id) ON DELETE CASCADE;

ALTER TABLE ONLY user_sessions
    ADD CONSTRAINT fk_session_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY system_settings
    ADD CONSTRAINT fk_setting_modified_by FOREIGN KEY (last_modified_by) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY staff
    ADD CONSTRAINT fk_staff_dept FOREIGN KEY (department_id) REFERENCES departments(department_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY staff
    ADD CONSTRAINT fk_staff_office FOREIGN KEY (office_room_id) REFERENCES rooms(room_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY staff
    ADD CONSTRAINT fk_staff_supervisor FOREIGN KEY (supervisor_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY staff
    ADD CONSTRAINT fk_staff_user FOREIGN KEY (staff_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY students
    ADD CONSTRAINT fk_student_advisor FOREIGN KEY (advisor_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY students
    ADD CONSTRAINT fk_student_program FOREIGN KEY (program_id) REFERENCES programs(program_id) ON DELETE CASCADE;

ALTER TABLE ONLY students
    ADD CONSTRAINT fk_student_term FOREIGN KEY (current_term_id) REFERENCES academic_terms(term_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY students
    ADD CONSTRAINT fk_student_user FOREIGN KEY (student_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY assignment_submissions
    ADD CONSTRAINT fk_sub_assignment FOREIGN KEY (assignment_id) REFERENCES assignments(assignment_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY assignment_submissions
    ADD CONSTRAINT fk_sub_graded_by FOREIGN KEY (graded_by) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY assignment_submissions
    ADD CONSTRAINT fk_sub_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY research_team_members
    ADD CONSTRAINT fk_team_project FOREIGN KEY (project_id) REFERENCES research_projects(project_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY research_team_members
    ADD CONSTRAINT fk_team_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY financial_transactions
    ADD CONSTRAINT fk_trans_account FOREIGN KEY (account_id) REFERENCES student_accounts(account_id) ON DELETE CASCADE;

ALTER TABLE ONLY financial_transactions
    ADD CONSTRAINT fk_trans_processed_by FOREIGN KEY (processed_by) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE ONLY financial_transactions
    ADD CONSTRAINT fk_trans_reversal FOREIGN KEY (reversal_transaction_id) REFERENCES financial_transactions(transaction_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY financial_transactions
    ADD CONSTRAINT fk_trans_term FOREIGN KEY (term_id) REFERENCES academic_terms(term_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY user_addresses
    ADD CONSTRAINT fk_ua_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY user_contact_info
    ADD CONSTRAINT fk_uci_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY user_emergency_contacts
    ADD CONSTRAINT fk_uec_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY user_preferences
    ADD CONSTRAINT fk_up_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY user_personal_info
    ADD CONSTRAINT fk_upi_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY user_role_assignments
    ADD CONSTRAINT fk_ura_assigned_by FOREIGN KEY (assigned_by) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY user_role_assignments
    ADD CONSTRAINT fk_ura_role FOREIGN KEY (role_id) REFERENCES user_roles(role_id) ON DELETE CASCADE;

ALTER TABLE ONLY user_role_assignments
    ADD CONSTRAINT fk_ura_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY reviews
    ADD CONSTRAINT reviews_course_id_fkey FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE SET NULL;

ALTER TABLE ONLY reviews
    ADD CONSTRAINT reviews_enrollment_id_fkey FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id) ON DELETE CASCADE;

ALTER TABLE ONLY reviews
    ADD CONSTRAINT reviews_faculty_id_fkey FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON DELETE CASCADE;

ALTER TABLE ONLY reviews
    ADD CONSTRAINT reviews_term_id_fkey FOREIGN KEY (term_id) REFERENCES academic_terms(term_id) ON DELETE SET NULL;

ALTER TABLE ONLY withdrawal_requests
    ADD CONSTRAINT withdrawal_requests_enrollment_id_fkey FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id) ON DELETE CASCADE;

ALTER TABLE ONLY withdrawal_requests
    ADD CONSTRAINT withdrawal_requests_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL;

ALTER TABLE ONLY withdrawal_requests
    ADD CONSTRAINT withdrawal_requests_student_id_fkey FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE;
