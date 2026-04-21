-- Socket Value Dashboard Schema
-- Stores time-series snapshots of Socket API data for Grafana

-- ─────────────────────────────────────────
-- Org-level score snapshots (trending over time)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS org_scores (
    id              SERIAL PRIMARY KEY,
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    org_slug        TEXT NOT NULL,
    avg_overall     FLOAT,
    avg_supply_chain FLOAT,
    avg_vulnerability FLOAT,
    avg_quality     FLOAT,
    avg_maintenance FLOAT,
    avg_license     FLOAT,
    total_packages  INT
);

-- ─────────────────────────────────────────
-- Per-package scores (for drill-down views)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS package_scores (
    id              SERIAL PRIMARY KEY,
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    org_slug        TEXT NOT NULL,
    package_name    TEXT NOT NULL,
    package_version TEXT,
    ecosystem       TEXT,
    score_overall   FLOAT,
    score_supply_chain FLOAT,
    score_vulnerability FLOAT,
    score_quality   FLOAT,
    score_maintenance FLOAT,
    score_license   FLOAT
);

-- ─────────────────────────────────────────
-- Alerts / issues by severity over time
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alert_counts (
    id              SERIAL PRIMARY KEY,
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    org_slug        TEXT NOT NULL,
    severity        TEXT NOT NULL,  -- critical, high, medium, low
    alert_type      TEXT,
    count           INT NOT NULL DEFAULT 0
);

-- ─────────────────────────────────────────
-- CVE tracking
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cve_findings (
    id              SERIAL PRIMARY KEY,
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    org_slug        TEXT NOT NULL,
    package_name    TEXT NOT NULL,
    cve_id          TEXT NOT NULL,
    cvss_score      FLOAT,
    severity        TEXT,
    is_fixable      BOOLEAN DEFAULT FALSE,
    first_seen_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- Dependency inventory snapshots
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dependency_inventory (
    id              SERIAL PRIMARY KEY,
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    org_slug        TEXT NOT NULL,
    total_direct    INT DEFAULT 0,
    total_transitive INT DEFAULT 0,
    total_unmaintained INT DEFAULT 0,
    total_deprecated INT DEFAULT 0,
    total_high_risk INT DEFAULT 0
);

-- ─────────────────────────────────────────
-- Indexes for Grafana time-series queries
-- ─────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_org_scores_time ON org_scores (collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_counts_time ON alert_counts (collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_cve_findings_time ON cve_findings (collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_package_scores_name ON package_scores (package_name, collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_dep_inventory_time ON dependency_inventory (collected_at DESC);
