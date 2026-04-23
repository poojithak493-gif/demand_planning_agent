CREATE TABLE IF NOT EXISTS inbound_mail_responses (
    id                  BIGSERIAL PRIMARY KEY,
    distributor_id      UUID,
    distributor_code    VARCHAR(50),
    from_email          VARCHAR(255),
    subject             TEXT,
    raw_body            TEXT NOT NULL,
    received_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processing_status   VARCHAR(50) NOT NULL,
    parse_status        VARCHAR(50) NOT NULL,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inbound_mail_responses_distributor_code
ON inbound_mail_responses (distributor_code);

CREATE INDEX IF NOT EXISTS idx_inbound_mail_responses_received_at
ON inbound_mail_responses (received_at DESC);

CREATE INDEX IF NOT EXISTS idx_inbound_mail_responses_processing_status
ON inbound_mail_responses (processing_status);


CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER set_updated_at_inbound_mail_responses
    BEFORE UPDATE ON inbound_mail_responses
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
