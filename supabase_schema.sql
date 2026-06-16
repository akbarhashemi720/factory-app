-- =============================================================
-- AI Factory — Supabase Schema  (Sprint 1)
-- =============================================================
-- Run this in the Supabase SQL Editor to create the two tables
-- needed for Sprint 1.
-- =============================================================

-- Enable the uuid-ossp extension so uuid_generate_v4() is available.
-- (Supabase projects have this enabled by default; safe to run again.)
create extension if not exists "uuid-ossp";

-- ─── projects ──────────────────────────────────────────────────
create table if not exists projects (
    id                    uuid primary key default uuid_generate_v4(),
    user_id               text,
    status                text not null default 'draft',
    scenario              text,
    language              text not null default 'fa',
    current_version_id    uuid,           -- filled in later sprints
    final_approval_status boolean not null default false,
    created_at            timestamptz not null default now(),
    updated_at            timestamptz not null default now()
);

comment on table  projects                       is 'One row per factory project.';
comment on column projects.status               is 'draft | waiting_for_user_confirmation | ready_for_builder | building | reviewing | ready_for_user_review | revision_requested | approved | archived';
comment on column projects.scenario             is 'Detected product scenario, e.g. restaurant, dashboard, business, birthday.';
comment on column projects.current_version_id  is 'FK to versions table (added in a later sprint).';

-- Auto-update updated_at on every row change.
create or replace function set_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trg_projects_updated_at on projects;
create trigger trg_projects_updated_at
before update on projects
for each row execute function set_updated_at();

-- ─── user_requests ─────────────────────────────────────────────
create table if not exists user_requests (
    id                uuid primary key default uuid_generate_v4(),
    project_id        uuid not null references projects(id) on delete cascade,
    raw_text          text not null,
    input_type        text not null default 'text',
    detected_language text not null default 'fa',
    attachments       jsonb not null default '[]',
    created_at        timestamptz not null default now()
);

comment on table  user_requests           is 'Raw user request tied to a project. Never modified after insert.';
comment on column user_requests.raw_text is 'Exact text as entered by the user — never altered by the system.';

-- Index for fast look-ups by project
create index if not exists idx_user_requests_project_id
    on user_requests (project_id);


-- =============================================================
-- Sprint 2 additions
-- =============================================================

-- ─── understandings ────────────────────────────────────────────
create table if not exists understandings (
    id                       uuid primary key default gen_random_uuid(),
    project_id               uuid not null references projects(id) on delete cascade,
    bullets                  jsonb not null default '[]',
    assumptions              jsonb not null default '[]',
    clarification_questions  jsonb not null default '[]',
    user_answers             jsonb not null default '[]',
    detected_scenario        text,
    confidence               text,
    confirmed_by_user        boolean not null default false,
    confirmed_at             timestamptz,
    created_at               timestamptz not null default now(),
    updated_at               timestamptz not null default now()
);

comment on table  understandings                     is 'PM Agent understanding of a user request. Must be confirmed before building.';
comment on column understandings.confirmed_by_user  is 'CRITICAL: building cannot start until this is true.';
comment on column understandings.confirmed_at       is 'Timestamp when user confirmed. Null if not yet confirmed.';

drop trigger if exists trg_understandings_updated_at on understandings;
create trigger trg_understandings_updated_at
before update on understandings
for each row execute function set_updated_at();

create index if not exists idx_understandings_project_id
    on understandings (project_id);


-- =============================================================
-- Sprint 3 additions
-- =============================================================

-- ─── builder_outputs ───────────────────────────────────────────
create table if not exists builder_outputs (
    id                  uuid primary key default gen_random_uuid(),
    project_id          uuid not null references projects(id) on delete cascade,
    version_id          uuid,
    output_type         text not null default 'preview_json',
    preview_data        jsonb not null default '{}',
    change_summary      jsonb not null default '[]',
    known_limitations   jsonb not null default '[]',
    created_at          timestamptz not null default now()
);

comment on table builder_outputs is 'Output produced by the Builder for a given project version.';
create index if not exists idx_builder_outputs_project_id on builder_outputs (project_id);

-- ─── versions ──────────────────────────────────────────────────
create table if not exists versions (
    id                   uuid primary key default gen_random_uuid(),
    project_id           uuid not null references projects(id) on delete cascade,
    version_number       integer not null,
    version_label        text not null default 'نسخه اول',
    output_id            uuid,
    review_report_id     uuid,
    user_visible_preview jsonb not null default '{}',
    approved_by_user     boolean not null default false,
    created_at           timestamptz not null default now()
);

comment on table  versions                    is 'One row per builder output version per project.';
comment on column versions.approved_by_user  is 'True only after explicit user final approval.';
create index if not exists idx_versions_project_id on versions (project_id);

-- ─── review_reports ────────────────────────────────────────────
create table if not exists review_reports (
    id                     uuid primary key default gen_random_uuid(),
    project_id             uuid not null references projects(id) on delete cascade,
    version_id             uuid,
    overall_status         text not null default 'passed',
    issues_found           jsonb not null default '[]',
    checklist              jsonb not null default '[]',
    user_friendly_summary  text,
    internal_notes         text,
    created_at             timestamptz not null default now()
);

comment on table  review_reports                     is 'Reviewer result. overall_status=passed does NOT mean user approval.';
comment on column review_reports.overall_status     is 'passed | needs_revision | blocked';
comment on column review_reports.user_friendly_summary is 'Simple text shown to user via PM Agent.';
create index if not exists idx_review_reports_project_id on review_reports (project_id);


-- =============================================================
-- Sprint 4A additions
-- =============================================================

-- ─── approved_versions ─────────────────────────────────────────
create table if not exists approved_versions (
    id              uuid primary key default gen_random_uuid(),
    project_id      uuid not null references projects(id) on delete cascade,
    version_id      uuid not null references versions(id) on delete cascade,
    approved_at     timestamptz not null default now(),
    user_feedback   text,
    final_summary   text
);

comment on table  approved_versions           is 'Records final user approval. One row per approved project version.';
comment on column approved_versions.version_id is 'The specific version the user approved.';
create index if not exists idx_approved_versions_project_id on approved_versions (project_id);

-- ─── learning_notes ────────────────────────────────────────────
create table if not exists learning_notes (
    id                        uuid primary key default gen_random_uuid(),
    project_id                uuid not null references projects(id) on delete cascade,
    version_id                uuid,
    scenario                  text,
    product_type              text not null default 'preview',
    what_worked               jsonb not null default '[]',
    user_preferences_detected jsonb not null default '{}',
    reusable_patterns         jsonb not null default '[]',
    created_at                timestamptz not null default now()
);

comment on table  learning_notes                          is 'What the factory learned after final user approval. Written by Memory Layer only.';
comment on column learning_notes.reusable_patterns       is 'Patterns that future Builder providers can read to start from proven structures.';
create index if not exists idx_learning_notes_project_id  on learning_notes (project_id);
create index if not exists idx_learning_notes_scenario    on learning_notes (scenario);


-- =============================================================
-- Sprint 4B additions
-- =============================================================

-- ─── revision_requests ─────────────────────────────────────────
create table if not exists revision_requests (
    id                   uuid primary key default gen_random_uuid(),
    project_id           uuid not null references projects(id) on delete cascade,
    from_version_id      uuid not null references versions(id) on delete cascade,
    raw_revision_text    text not null,
    interpreted_actions  jsonb not null default '[]',
    status               text not null default 'pending',
    created_at           timestamptz not null default now(),
    updated_at           timestamptz not null default now()
);

comment on table  revision_requests                  is 'User correction requests. Applied by the Builder to produce a new version.';
comment on column revision_requests.status          is 'pending | applied | rejected';
comment on column revision_requests.from_version_id is 'The version the user was looking at when they requested the change.';
comment on column revision_requests.interpreted_actions is 'Structured actions derived from raw_revision_text by the revision service.';

drop trigger if exists trg_revision_requests_updated_at on revision_requests;
create trigger trg_revision_requests_updated_at
before update on revision_requests
for each row execute function set_updated_at();

create index if not exists idx_revision_requests_project_id on revision_requests (project_id);
create index if not exists idx_revision_requests_status     on revision_requests (status);


-- =============================================================
-- Sprint 5 additions
-- =============================================================

-- ─── reusable_patterns ─────────────────────────────────────────
create table if not exists reusable_patterns (
    id                  uuid primary key default gen_random_uuid(),
    scenario            text not null,
    pattern_type        text not null default 'approved_preview_pattern',
    source_project_id   uuid references projects(id) on delete set null,
    source_version_id   uuid references versions(id) on delete set null,
    title               text,
    pattern_data        jsonb not null default '{}',
    usage_count         integer not null default 0,
    approval_count      integer not null default 1,
    created_at          timestamptz not null default now(),
    updated_at          timestamptz not null default now()
);

comment on table reusable_patterns is 'Scenario-based patterns extracted from approved projects. Used by future Builder providers to start from proven structures.';
comment on column reusable_patterns.usage_count    is 'How many times this pattern was used as a starting point for a new project.';
comment on column reusable_patterns.approval_count is 'How many times a project built on this pattern was approved.';

drop trigger if exists trg_reusable_patterns_updated_at on reusable_patterns;
create trigger trg_reusable_patterns_updated_at
before update on reusable_patterns
for each row execute function set_updated_at();

create index if not exists idx_reusable_patterns_scenario on reusable_patterns (scenario);


-- =============================================================
-- Sprint 9 additions
-- =============================================================

-- ─── exports ───────────────────────────────────────────────────
create table if not exists exports (
    id           uuid primary key default gen_random_uuid(),
    project_id   uuid not null references projects(id) on delete cascade,
    version_id   uuid not null references versions(id) on delete cascade,
    export_type  text not null default 'preview_package',
    export_data  jsonb not null default '{}',
    summary      text,
    created_at   timestamptz not null default now()
);

comment on table  exports             is 'Export packages created from approved project versions. Not full deployment — used for demo, handoff, and future production build.';
comment on column exports.export_type is 'preview_package (MVP) | future: html_bundle, app_package, ...';
comment on column exports.export_data is 'Clean structured data ready for downstream use. No raw DB internals.';

create index if not exists idx_exports_project_id on exports (project_id);


-- =============================================================
-- Customer Account Layer — MVP ownership foundation
-- =============================================================
-- customer_id is NOT production auth. It is an MVP ownership
-- identifier so future layers (Consent, Agents, Audit, Handoff)
-- can safely scope data to a customer.

alter table projects
  add column if not exists customer_id text;

comment on column projects.customer_id is
  'MVP ownership identifier. Generated by factory if not provided. '
  'Not real auth — foundation for future Consent Hub and agent scope.';

create index if not exists idx_projects_customer_id
  on projects (customer_id);
