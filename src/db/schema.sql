CREATE TABLE IF NOT EXISTS drafts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    story_text      TEXT    NOT NULL,
    caption_draft   TEXT    NOT NULL,
    selected_images TEXT,           -- JSON array of file paths
    story_analysis  TEXT,           -- JSON object
    status          TEXT    NOT NULL DEFAULT 'draft',
    post_result     TEXT,           -- JSON object from Facebook API response
    created_at      TEXT    NOT NULL,
    updated_at      TEXT
);
