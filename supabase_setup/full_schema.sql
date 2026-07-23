-- ============================================================
-- module1_tables.sql — Bảng bổ sung cho Module 1
-- Chạy trong Supabase SQL Editor
-- Bảng profiles đã có sẵn trong Supabase Auth
-- ============================================================

-- Bảng lời mời đăng ký
CREATE TABLE IF NOT EXISTS public.invitations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT NOT NULL,
    full_name   TEXT NOT NULL,
    token       UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    invited_by  UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    used        BOOLEAN DEFAULT FALSE,
    used_at     TIMESTAMPTZ,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_invitations_email ON public.invitations(email);
CREATE INDEX IF NOT EXISTS idx_invitations_token ON public.invitations(token);

-- Bảng OTP xác nhận đăng ký
CREATE TABLE IF NOT EXISTS public.otp_codes (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email             TEXT NOT NULL,
    code              VARCHAR(4) NOT NULL,
    invitation_token  UUID,
    expires_at        TIMESTAMPTZ NOT NULL,
    used              BOOLEAN DEFAULT FALSE,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_otp_email ON public.otp_codes(email);

-- Bật RLS (service role key bypass, anon không truy cập được)
ALTER TABLE public.invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.otp_codes ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- full_schema.sql — Toàn bộ schema cho webnoibo
-- (Chạy nếu đây là Supabase project mới, chưa có bảng nào)
-- ============================================================

-- Profiles (mở rộng từ auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
    full_name   TEXT,
    role        TEXT CHECK (role IN ('admin','leader','member')) DEFAULT 'member',
    department  TEXT,
    bio         TEXT,
    github_url  TEXT,
    phone       TEXT,
    status      TEXT DEFAULT 'active',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Dự án
CREATE TABLE IF NOT EXISTS public.projects (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    description TEXT,
    deadline    DATE,
    status      TEXT CHECK (status IN ('planning','in_progress','review','completed','paused')) DEFAULT 'planning',
    priority    TEXT CHECK (priority IN ('low','medium','high','critical')) DEFAULT 'medium',
    created_by  UUID REFERENCES public.profiles(id),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Thành viên dự án
CREATE TABLE IF NOT EXISTS public.project_members (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    member_id   UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    role        TEXT DEFAULT 'member',
    UNIQUE(project_id, member_id)
);

-- Công việc (Tasks)
CREATE TABLE IF NOT EXISTS public.tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    description     TEXT,
    assignee_id     UUID REFERENCES public.profiles(id),
    deadline        DATE,
    status          TEXT CHECK (status IN ('todo','doing','review','done','blocked','cancelled')) DEFAULT 'todo',
    priority        TEXT CHECK (priority IN ('low','medium','high','critical')) DEFAULT 'medium',
    progress        INTEGER DEFAULT 0,
    checklist       JSONB DEFAULT '[]',
    notes           TEXT,
    attachment_url  TEXT,
    column_order    INTEGER DEFAULT 0,
    created_by      UUID REFERENCES public.profiles(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON public.tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON public.tasks(assignee_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON public.tasks(status);

-- Bật RLS cho tất cả bảng nghiệp vụ
ALTER TABLE public.profiles      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks          ENABLE ROW LEVEL SECURITY;

-- Trigger cập nhật updated_at tự động
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_projects_updated BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_tasks_updated BEFORE UPDATE ON public.tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Trigger tự động tạo profile khi có user mới
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name)
    VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name')
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();
