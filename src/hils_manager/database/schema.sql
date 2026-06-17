-- HILS Manager Database Schema
-- SQLite DDL for automotive embedded test development project management

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ============================================================
-- Team Members
-- ============================================================
CREATE TABLE IF NOT EXISTS team_members (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT    UNIQUE NOT NULL,
    name        TEXT    NOT NULL,
    email       TEXT,
    is_outsourced INTEGER DEFAULT 0,
    daily_rate  REAL,
    skills      TEXT,       -- JSON array of skill strings
    is_active   INTEGER DEFAULT 1,
    created_at  TEXT    DEFAULT (datetime('now')),
    updated_at  TEXT    DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_team_members_active ON team_members(is_active);
CREATE INDEX IF NOT EXISTS idx_team_members_outsourced ON team_members(is_outsourced);

-- ============================================================
-- Projects
-- ============================================================
CREATE TABLE IF NOT EXISTS projects (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code     TEXT    UNIQUE NOT NULL,
    name             TEXT    NOT NULL,
    description      TEXT,
    status           TEXT    DEFAULT 'planning'
                             CHECK (status IN ('planning', 'active', 'on_hold', 'completed', 'cancelled')),
    start_date       TEXT,
    end_date         TEXT,
    actual_start     TEXT,
    actual_end       TEXT,
    jira_project_key TEXT,
    created_at       TEXT    DEFAULT (datetime('now')),
    updated_at       TEXT    DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_jira ON projects(jira_project_key);

-- ============================================================
-- Project Assignments
-- ============================================================
CREATE TABLE IF NOT EXISTS project_assignments (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    member_id      INTEGER NOT NULL REFERENCES team_members(id) ON DELETE CASCADE,
    role           TEXT    NOT NULL
                           CHECK (role IN ('development_owner', 'development_leader',
                                           'member_manager', 'primary_developer',
                                           'cross_developer')),
    allocation_pct REAL    DEFAULT 100.0,
    start_date     TEXT,
    end_date       TEXT,
    UNIQUE (project_id, member_id, role)
);

CREATE INDEX IF NOT EXISTS idx_project_assignments_project ON project_assignments(project_id);
CREATE INDEX IF NOT EXISTS idx_project_assignments_member ON project_assignments(member_id);

-- ============================================================
-- Process Definitions (master list of development processes)
-- ============================================================
CREATE TABLE IF NOT EXISTS process_definitions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    code       TEXT    UNIQUE NOT NULL,
    name_ja    TEXT    NOT NULL,
    name_en    TEXT    NOT NULL,
    phase      TEXT    NOT NULL,
    sort_order INTEGER NOT NULL,
    is_default INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_process_definitions_phase ON process_definitions(phase);

-- ============================================================
-- Process Selections (per-project process tailoring)
-- ============================================================
CREATE TABLE IF NOT EXISTS process_selections (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    process_def_id INTEGER NOT NULL REFERENCES process_definitions(id) ON DELETE CASCADE,
    is_selected    INTEGER DEFAULT 1,
    skip_reason    TEXT,
    UNIQUE (project_id, process_def_id)
);

CREATE INDEX IF NOT EXISTS idx_process_selections_project ON process_selections(project_id);

-- ============================================================
-- Deliverables
-- ============================================================
CREATE TABLE IF NOT EXISTS deliverables (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    process_def_id INTEGER REFERENCES process_definitions(id) ON DELETE SET NULL,
    title          TEXT    NOT NULL,
    status         TEXT    DEFAULT 'not_started'
                           CHECK (status IN ('not_started', 'in_progress', 'in_review',
                                             'approved', 'rejected')),
    assigned_to    INTEGER REFERENCES team_members(id) ON DELETE SET NULL,
    due_date       TEXT,
    completed_date TEXT,
    file_path      TEXT,
    content_json   TEXT,
    version        INTEGER DEFAULT 1,
    created_at     TEXT    DEFAULT (datetime('now')),
    updated_at     TEXT    DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_deliverables_project ON deliverables(project_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_status ON deliverables(status);
CREATE INDEX IF NOT EXISTS idx_deliverables_assigned ON deliverables(assigned_to);

-- ============================================================
-- Deliverable Reviews
-- ============================================================
CREATE TABLE IF NOT EXISTS deliverable_reviews (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    deliverable_id INTEGER NOT NULL REFERENCES deliverables(id) ON DELETE CASCADE,
    review_type    TEXT    NOT NULL
                           CHECK (review_type IN ('pre_delivery', 'owner_briefing', 'peer_review')),
    reviewer_id    INTEGER REFERENCES team_members(id) ON DELETE SET NULL,
    status         TEXT    DEFAULT 'pending'
                           CHECK (status IN ('pending', 'approved', 'rejected', 'conditional')),
    comments       TEXT,
    review_date    TEXT,
    created_at     TEXT    DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_deliverable_reviews_deliverable ON deliverable_reviews(deliverable_id);
CREATE INDEX IF NOT EXISTS idx_deliverable_reviews_reviewer ON deliverable_reviews(reviewer_id);

-- ============================================================
-- Requirements
-- ============================================================
CREATE TABLE IF NOT EXISTS requirements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    req_number      TEXT    NOT NULL,
    title           TEXT    NOT NULL,
    description     TEXT,
    priority        TEXT    DEFAULT 'medium'
                            CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    status          TEXT    DEFAULT 'new'
                            CHECK (status IN ('new', 'accepted', 'in_progress',
                                              'implemented', 'verified', 'deferred', 'rejected')),
    requested_by    TEXT,
    requested_date  TEXT,
    target_version  TEXT,
    created_at      TEXT    DEFAULT (datetime('now')),
    updated_at      TEXT    DEFAULT (datetime('now')),
    UNIQUE (project_id, req_number)
);

CREATE INDEX IF NOT EXISTS idx_requirements_project ON requirements(project_id);
CREATE INDEX IF NOT EXISTS idx_requirements_status ON requirements(status);
CREATE INDEX IF NOT EXISTS idx_requirements_priority ON requirements(priority);

-- ============================================================
-- WBS Items
-- ============================================================
CREATE TABLE IF NOT EXISTS wbs_items (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parent_id      INTEGER REFERENCES wbs_items(id) ON DELETE SET NULL,
    wbs_code       TEXT    NOT NULL,
    title          TEXT    NOT NULL,
    description    TEXT,
    assigned_to    INTEGER REFERENCES team_members(id) ON DELETE SET NULL,
    status         TEXT    DEFAULT 'not_started'
                           CHECK (status IN ('not_started', 'in_progress', 'completed',
                                             'blocked', 'cancelled')),
    planned_start  TEXT,
    planned_end    TEXT,
    actual_start   TEXT,
    actual_end     TEXT,
    planned_hours  REAL,
    dependency_ids TEXT,    -- JSON array of wbs_item ids
    sort_order     INTEGER DEFAULT 0,
    jira_issue_key TEXT,
    created_at     TEXT    DEFAULT (datetime('now')),
    updated_at     TEXT    DEFAULT (datetime('now')),
    UNIQUE (project_id, wbs_code)
);

CREATE INDEX IF NOT EXISTS idx_wbs_items_project ON wbs_items(project_id);
CREATE INDEX IF NOT EXISTS idx_wbs_items_parent ON wbs_items(parent_id);
CREATE INDEX IF NOT EXISTS idx_wbs_items_assigned ON wbs_items(assigned_to);
CREATE INDEX IF NOT EXISTS idx_wbs_items_status ON wbs_items(status);

-- ============================================================
-- Estimates
-- ============================================================
CREATE TABLE IF NOT EXISTS estimates (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    wbs_item_id    INTEGER REFERENCES wbs_items(id) ON DELETE SET NULL,
    estimate_type  TEXT    NOT NULL
                           CHECK (estimate_type IN ('initial', 'revised', 'final')),
    man_hours      REAL    NOT NULL,
    lead_time_days INTEGER,
    estimator_id   INTEGER REFERENCES team_members(id) ON DELETE SET NULL,
    assumptions    TEXT,
    created_at     TEXT    DEFAULT (datetime('now')),
    UNIQUE (project_id, wbs_item_id, estimate_type)
);

CREATE INDEX IF NOT EXISTS idx_estimates_project ON estimates(project_id);
CREATE INDEX IF NOT EXISTS idx_estimates_wbs ON estimates(wbs_item_id);

-- ============================================================
-- Time Entries
-- ============================================================
CREATE TABLE IF NOT EXISTS time_entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    wbs_item_id INTEGER REFERENCES wbs_items(id) ON DELETE SET NULL,
    member_id   INTEGER NOT NULL REFERENCES team_members(id) ON DELETE CASCADE,
    work_date   TEXT    NOT NULL,
    hours       REAL    NOT NULL,
    description TEXT,
    created_at  TEXT    DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_time_entries_project ON time_entries(project_id);
CREATE INDEX IF NOT EXISTS idx_time_entries_member ON time_entries(member_id);
CREATE INDEX IF NOT EXISTS idx_time_entries_date ON time_entries(work_date);
CREATE INDEX IF NOT EXISTS idx_time_entries_wbs ON time_entries(wbs_item_id);

-- ============================================================
-- Risks
-- ============================================================
CREATE TABLE IF NOT EXISTS risks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    risk_number     TEXT    NOT NULL,
    title           TEXT    NOT NULL,
    description     TEXT,
    probability     TEXT    DEFAULT 'medium'
                            CHECK (probability IN ('high', 'medium', 'low')),
    impact          TEXT    DEFAULT 'medium'
                            CHECK (impact IN ('high', 'medium', 'low')),
    mitigation      TEXT    NOT NULL,
    status          TEXT    DEFAULT 'open'
                            CHECK (status IN ('open', 'mitigating', 'resolved', 'accepted')),
    owner_id        INTEGER REFERENCES team_members(id) ON DELETE SET NULL,
    identified_date TEXT    NOT NULL,
    target_date     TEXT,
    resolution_date TEXT,
    created_at      TEXT    DEFAULT (datetime('now')),
    updated_at      TEXT    DEFAULT (datetime('now')),
    UNIQUE (project_id, risk_number)
);

CREATE INDEX IF NOT EXISTS idx_risks_project ON risks(project_id);
CREATE INDEX IF NOT EXISTS idx_risks_status ON risks(status);
CREATE INDEX IF NOT EXISTS idx_risks_owner ON risks(owner_id);

-- ============================================================
-- Dankomi Records (milestone kick-off meeting records)
-- ============================================================
CREATE TABLE IF NOT EXISTS dankomi_records (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id       INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    meeting_date     TEXT    NOT NULL,
    attendees        TEXT    NOT NULL,
    goal_state       TEXT,
    goal_deliverables TEXT,
    agenda           TEXT,
    decisions        TEXT,
    action_items     TEXT,
    notes            TEXT,
    created_at       TEXT    DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_dankomi_records_project ON dankomi_records(project_id);

-- ============================================================
-- Jira Sync Mappings
-- ============================================================
CREATE TABLE IF NOT EXISTS jira_sync_mappings (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    local_entity   TEXT    NOT NULL,
    local_id       INTEGER NOT NULL,
    jira_issue_key TEXT    NOT NULL,
    jira_issue_id  TEXT,
    last_sync_at   TEXT,
    sync_direction TEXT    DEFAULT 'bidirectional'
                           CHECK (sync_direction IN ('push_only', 'pull_only', 'bidirectional')),
    sync_status    TEXT    DEFAULT 'synced'
                           CHECK (sync_status IN ('synced', 'local_modified', 'remote_modified', 'conflict')),
    UNIQUE (local_entity, local_id),
    UNIQUE (jira_issue_key)
);

CREATE INDEX IF NOT EXISTS idx_jira_sync_mappings_project ON jira_sync_mappings(project_id);
CREATE INDEX IF NOT EXISTS idx_jira_sync_mappings_status ON jira_sync_mappings(sync_status);

-- ============================================================
-- Jira Sync Log
-- ============================================================
CREATE TABLE IF NOT EXISTS jira_sync_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    mapping_id INTEGER NOT NULL REFERENCES jira_sync_mappings(id) ON DELETE CASCADE,
    sync_type  TEXT    NOT NULL
                       CHECK (sync_type IN ('push', 'pull')),
    status     TEXT    NOT NULL
                       CHECK (status IN ('success', 'error', 'conflict')),
    details    TEXT,
    synced_at  TEXT    DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_jira_sync_log_mapping ON jira_sync_log(mapping_id);

-- ============================================================
-- Outsource Billing
-- ============================================================
CREATE TABLE IF NOT EXISTS outsource_billing (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id     INTEGER NOT NULL REFERENCES team_members(id) ON DELETE CASCADE,
    project_id    INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    billing_month TEXT    NOT NULL,
    man_days      REAL    NOT NULL,
    daily_rate    REAL    NOT NULL,
    total_amount  REAL    NOT NULL,
    notes         TEXT,
    created_at    TEXT    DEFAULT (datetime('now')),
    UNIQUE (member_id, project_id, billing_month)
);

CREATE INDEX IF NOT EXISTS idx_outsource_billing_member ON outsource_billing(member_id);
CREATE INDEX IF NOT EXISTS idx_outsource_billing_project ON outsource_billing(project_id);
CREATE INDEX IF NOT EXISTS idx_outsource_billing_month ON outsource_billing(billing_month);

-- ============================================================
-- Reports
-- ============================================================
CREATE TABLE IF NOT EXISTS reports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    report_type     TEXT    NOT NULL
                            CHECK (report_type IN ('detailed', 'summary', 'weekly', 'monthly', 'annual')),
    format          TEXT    NOT NULL
                            CHECK (format IN ('html', 'confluence')),
    title           TEXT    NOT NULL,
    generated_by    INTEGER REFERENCES team_members(id) ON DELETE SET NULL,
    file_path       TEXT,
    confluence_url  TEXT,
    parameters_json TEXT,
    generated_at    TEXT    DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_reports_project ON reports(project_id);
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type);

-- ============================================================
-- Application Settings (key-value store)
-- ============================================================
CREATE TABLE IF NOT EXISTS app_settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    description TEXT
);

-- ============================================================
-- Seed Data: Process Definitions
-- ============================================================
INSERT OR IGNORE INTO process_definitions (code, name_ja, name_en, phase, sort_order) VALUES
    ('requirements_list',   '要望リスト',         'Requirements List',    'planning',        10),
    ('requirements_spec',   '要件定義書',         'Requirements Specification', 'planning',   20),
    ('estimate',            '見積書',             'Estimate',             'planning',        30),
    ('dankomi',             '段コミ',             'Dankomi Kickoff',      'planning',        40),
    ('plan_review',         '計画レビュー',       'Plan Review',          'planning',        50),
    ('design_doc',          '設計書',             'Design Document',      'design',          60),
    ('timing_chart',        'タイミングチャート', 'Timing Chart',         'design',          70),
    ('hils_architecture',   'HILS構成図',         'HILS Architecture',    'design',          80),
    ('sequence_diagram',    'シーケンス図',       'Sequence Diagram',     'design',          90),
    ('user_config',         'ユーザコンフィグ',   'User Configuration',   'design',         100),
    ('test_spec',           'テスト仕様書',       'Test Specification',   'design',         110),
    ('implementation',      '実装',               'Implementation',       'implementation', 120),
    ('test_results',        'テスト結果',         'Test Results',         'test',           130),
    ('pre_delivery_review', '納品前レビュー',     'Pre-Delivery Review',  'delivery',       140),
    ('owner_briefing',      'オーナー説明',       'Owner Briefing',       'delivery',       150),
    ('user_manual',         'ユーザマニュアル',   'User Manual',          'delivery',       160);
