-- =============================================================
-- DEMAND PLANNING AGENT — PostgreSQL Schema
-- demand_planning.sql
-- =============================================================
-- Tables:
--   1. distributors
--   2. skus
--   3. distributor_skus        (many-to-many mapping)
--   4. demand_cycles           (monthly cycle tracker)
--   5. primary_sales           (raw cleaned data from CSV)
--   6. demand_records          (confirmed demand per cycle)
--   7. validation_results      (validation layer output)
--   8. review_queue            (failed validations pending review)
-- =============================================================

-- -------------------------------------------------------------
-- EXTENSIONS
-- -------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- for uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- for fuzzy text search on email replies


-- =============================================================
-- 1. DISTRIBUTORS
-- Master table of all distributors in the system.
-- =============================================================
CREATE TABLE IF NOT EXISTS distributors (
    distributor_id      UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    distributor_code    VARCHAR(50)     NOT NULL UNIQUE,   -- e.g. "DIST_001"
    name                VARCHAR(255)    NOT NULL,
    email               VARCHAR(255)    NOT NULL UNIQUE,
    phone               VARCHAR(30),
    region              VARCHAR(100),
    priority            VARCHAR(10)     NOT NULL CHECK (priority IN ('High', 'Medium', 'Low')),
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_distributors_code     ON distributors (distributor_code);
CREATE INDEX idx_distributors_priority ON distributors (priority);
CREATE INDEX idx_distributors_active   ON distributors (is_active);


-- =============================================================
-- 2. SKUs
-- Master catalogue of all SKUs tracked in demand planning.
-- =============================================================
CREATE TABLE IF NOT EXISTS skus (
    sku_id          UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    sku_code        VARCHAR(100)    NOT NULL UNIQUE,   -- e.g. "SKU_A1"
    sku_name        VARCHAR(255)    NOT NULL,
    category        VARCHAR(100),
    unit_of_measure VARCHAR(50)     NOT NULL DEFAULT 'units',
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_skus_code     ON skus (sku_code);
CREATE INDEX idx_skus_category ON skus (category);


-- =============================================================
-- 3. DISTRIBUTOR_SKUS
-- Many-to-many: which SKUs a distributor handles.
-- Mirrors the Distributor ⇌ SKU edges in FalkorDB.
-- =============================================================
CREATE TABLE IF NOT EXISTS distributor_skus (
    id              UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    distributor_id  UUID    NOT NULL REFERENCES distributors (distributor_id) ON DELETE CASCADE,
    sku_id          UUID    NOT NULL REFERENCES skus (sku_id) ON DELETE CASCADE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    assigned_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_distributor_sku UNIQUE (distributor_id, sku_id)
);

CREATE INDEX idx_dist_skus_distributor ON distributor_skus (distributor_id);
CREATE INDEX idx_dist_skus_sku         ON distributor_skus (sku_id);


-- =============================================================
-- 4. DEMAND_CYCLES
-- One row per monthly demand planning cycle.
-- Inngest triggers a new cycle each month.
-- =============================================================
CREATE TABLE IF NOT EXISTS demand_cycles (
    cycle_id        UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    cycle_date      DATE        NOT NULL UNIQUE,           -- first day of the month, e.g. 2026-04-01
    cycle_label     VARCHAR(50) NOT NULL,                  -- e.g. "April 2026"
    status          VARCHAR(20) NOT NULL DEFAULT 'open'
                        CHECK (status IN ('open', 'in_progress', 'closed')),
    started_at      TIMESTAMPTZ,
    closed_at       TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_demand_cycles_date   ON demand_cycles (cycle_date);
CREATE INDEX idx_demand_cycles_status ON demand_cycles (status);


-- =============================================================
-- 5. PRIMARY_SALES
-- Cleaned historical sales records loaded from Primary_Sales.xlsx.
-- Source of truth for SKU recommendation logic.
-- =============================================================
CREATE TABLE IF NOT EXISTS primary_sales (
    sale_id         UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    distributor_id  UUID        NOT NULL REFERENCES distributors (distributor_id),
    sku_id          UUID        NOT NULL REFERENCES skus (sku_id),
    cycle_id        UUID        NOT NULL REFERENCES demand_cycles (cycle_id),

    -- Raw sales quantities
    sales_qty       NUMERIC(12, 2) NOT NULL CHECK (sales_qty >= 0),

    -- Demand planning breakdown (30-day confirmed qty split into 4 weeks)
    confirmed_30d_qty   NUMERIC(12, 2)  CHECK (confirmed_30d_qty >= 0),
    week1_qty           NUMERIC(12, 2)  CHECK (week1_qty >= 0),
    week2_qty           NUMERIC(12, 2)  CHECK (week2_qty >= 0),
    week3_qty           NUMERIC(12, 2)  CHECK (week3_qty >= 0),
    week4_qty           NUMERIC(12, 2)  CHECK (week4_qty >= 0),

    -- Validation
    validation_status   VARCHAR(20) NOT NULL DEFAULT 'pending'
                            CHECK (validation_status IN ('pending', 'passed', 'failed', 'under_review')),

    sale_date       DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_primary_sales_dist_sku_cycle UNIQUE (distributor_id, sku_id, cycle_id)
);

CREATE INDEX idx_primary_sales_distributor  ON primary_sales (distributor_id);
CREATE INDEX idx_primary_sales_sku          ON primary_sales (sku_id);
CREATE INDEX idx_primary_sales_cycle        ON primary_sales (cycle_id);
CREATE INDEX idx_primary_sales_val_status   ON primary_sales (validation_status);


-- =============================================================
-- 6. DEMAND_RECORDS
-- One row per distributor per SKU per cycle.
-- Written by demand_planning_service after reply is parsed.
-- Read by Metabase for the business dashboard.
-- =============================================================
CREATE TABLE IF NOT EXISTS demand_records (
    demand_id               UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    distributor_id          UUID        NOT NULL REFERENCES distributors (distributor_id),
    sku_id                  UUID        NOT NULL REFERENCES skus (sku_id),
    cycle_id                UUID        NOT NULL REFERENCES demand_cycles (cycle_id),

    -- Suggested by sku_recommendation_engine
    suggested_qty           NUMERIC(12, 2) NOT NULL CHECK (suggested_qty >= 0),

    -- Confirmed by distributor via email reply (parse_text / parse_excel)
    confirmed_qty           NUMERIC(12, 2)          CHECK (confirmed_qty >= 0),

    -- Weekly breakdown (demand_planning_service writes these)
    confirmed_30d_qty       NUMERIC(12, 2)          CHECK (confirmed_30d_qty >= 0),
    week1_qty               NUMERIC(12, 2)          CHECK (week1_qty >= 0),
    week2_qty               NUMERIC(12, 2)          CHECK (week2_qty >= 0),
    week3_qty               NUMERIC(12, 2)          CHECK (week3_qty >= 0),
    week4_qty               NUMERIC(12, 2)          CHECK (week4_qty >= 0),

    -- Workflow state
    demand_status_locked    BOOLEAN     NOT NULL DEFAULT FALSE,
    reply_latency_days      NUMERIC(5, 2),           -- days between email sent and reply received

    -- Email tracking
    email_sent_at           TIMESTAMPTZ,
    reply_received_at       TIMESTAMPTZ,
    resend_message_id       VARCHAR(255),            -- Resend delivery ID

    -- Validation
    validation_status       VARCHAR(20) NOT NULL DEFAULT 'pending'
                                CHECK (validation_status IN ('pending', 'passed', 'failed', 'under_review')),

    -- Temporal workflow
    temporal_workflow_id    VARCHAR(255),            -- for resuming after reply

    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_demand_dist_sku_cycle UNIQUE (distributor_id, sku_id, cycle_id)
);

CREATE INDEX idx_demand_records_distributor     ON demand_records (distributor_id);
CREATE INDEX idx_demand_records_sku             ON demand_records (sku_id);
CREATE INDEX idx_demand_records_cycle           ON demand_records (cycle_id);
CREATE INDEX idx_demand_records_status_locked   ON demand_records (demand_status_locked);
CREATE INDEX idx_demand_records_val_status      ON demand_records (validation_status);
CREATE INDEX idx_demand_records_email_sent      ON demand_records (email_sent_at);


-- =============================================================
-- 7. VALIDATION_RESULTS
-- Output of the validation_service for each demand record.
-- Failed records trigger the review queue.
-- =============================================================
CREATE TABLE IF NOT EXISTS validation_results (
    validation_id       UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    demand_id           UUID        NOT NULL REFERENCES demand_records (demand_id) ON DELETE CASCADE,

    -- Checks (TRUE = passed)
    sku_valid           BOOLEAN     NOT NULL DEFAULT FALSE,
    distributor_valid   BOOLEAN     NOT NULL DEFAULT FALSE,
    qty_sanity_passed   BOOLEAN     NOT NULL DEFAULT FALSE,   -- no negatives, no impossible spikes
    duplicate_check     BOOLEAN     NOT NULL DEFAULT FALSE,
    format_check        BOOLEAN     NOT NULL DEFAULT FALSE,

    -- Overall result
    overall_status      VARCHAR(20) NOT NULL DEFAULT 'pending'
                            CHECK (overall_status IN ('pending', 'passed', 'failed')),

    failure_reason      TEXT,                                 -- human-readable reason if failed
    validated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_validation_demand     ON validation_results (demand_id);
CREATE INDEX idx_validation_status     ON validation_results (overall_status);


-- =============================================================
-- 8. REVIEW_QUEUE
-- Holds demand records that failed validation.
-- Human reviews and either approves or rejects.
-- =============================================================
CREATE TABLE IF NOT EXISTS review_queue (
    review_id       UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    demand_id       UUID        NOT NULL REFERENCES demand_records (demand_id) ON DELETE CASCADE,
    validation_id   UUID        NOT NULL REFERENCES validation_results (validation_id),

    failure_summary TEXT        NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'approved', 'rejected')),

    reviewed_by     VARCHAR(255),
    reviewed_at     TIMESTAMPTZ,
    review_notes    TEXT,

    queued_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_review_queue_demand  ON review_queue (demand_id);
CREATE INDEX idx_review_queue_status  ON review_queue (status);


-- =============================================================
-- AUTO-UPDATE updated_at TRIGGER
-- Keeps updated_at current on every row update.
-- =============================================================
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_distributors
    BEFORE UPDATE ON distributors
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_skus
    BEFORE UPDATE ON skus
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_primary_sales
    BEFORE UPDATE ON primary_sales
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_demand_records
    BEFORE UPDATE ON demand_records
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();


-- =============================================================
-- DONE
-- To apply: psql -U postgres -d demand_planning -f demand_planning.sql
-- Or inside Docker: docker exec -i <postgres_container> psql -U postgres -d demand_planning -f /demand_planning.sql
-- =============================================================