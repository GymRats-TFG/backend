CREATE TABLE profiles (
    -- UUID es un tipo de dato válido en PostgreSQL
    id UUID PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
    username VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(50),
    -- Tipos de cuenta que pueden haber
    role VARCHAR(10) CHECK (role IN ('user', 'enterprise')),
    description TEXT,
    avatar_url TEXT,
    -- TZ en TIMESTAMP nos permite agregar la hora y no solo la fecha
    created_at TIMESTAMPTZ DEFAULT now()
);