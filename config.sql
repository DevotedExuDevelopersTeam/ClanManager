CREATE TABLE IF NOT EXISTS bans
(
    id
    INT
    UNIQUE
    NOT
    NULL,
    banned_until
    FLOAT
    NOT
    NULL
);

CREATE TABLE IF NOT EXISTS ids
(
    id
    INT
    UNIQUE
    NOT
    NULL,
    pg_id
    INT
);
