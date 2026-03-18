CREATE TABLE access_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    gym_id UUID REFERENCES gyms(id) ON DELETE CASCADE,
    action_type VARCHAR(10) CHECK (action_type IN ('entry', 'exit')),
    recorded_at TIMESTAMPTZ DEFAULT now()
);