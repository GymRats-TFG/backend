CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    gym_id UUID REFERENCES gyms(id) ON DELETE CASCADE,
    status VARCHAR(20) CHECK (status IN ('active', 'inactive', 'pending')),
    -- Usamos DATE para evitar errores con el servidor al usar TIMESTAMP
    start_date DATE DEFAULT CURRENT_DATE,
    expiration_date DATE
);