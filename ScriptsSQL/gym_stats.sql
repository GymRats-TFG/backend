CREATE TABLE gym_stats (
    gym_id UUID PRIMARY KEY REFERENCES gyms(id) ON DELETE CASCADE,
    current_capacity INT DEFAULT 0,
    last_update TIMESTAMPTZ DEFAULT now()
);