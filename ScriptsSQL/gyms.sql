CREATE TABLE gyms(
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    description TEXT,
    image_url TEXT,
    price DECIMAL(10,2),
    is_open BOOLEAN DEFAULT false
);