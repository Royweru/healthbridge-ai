-- PostgreSQL Database Schema for HealthBridge AI

-- Drop tables if they exist to ensure a clean slate
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS agents;

-- Table: patients
-- Stores patient information.
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(25) UNIQUE NOT NULL,
    name VARCHAR(100),
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: appointments
-- Stores appointment details for patients.
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    appointment_time TIMESTAMP WITH TIME ZONE NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'canceled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: agents
-- Stores information about the AI agents in the system.
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    role TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: messages
-- Logs all incoming and outgoing messages for audit and training purposes.
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE SET NULL,
    session_id VARCHAR(100), -- Could be phone number or another unique identifier for the conversation
    sender VARCHAR(50) NOT NULL, -- 'patient' or agent's name
    content TEXT NOT NULL,
    translated_content TEXT,
    language VARCHAR(10),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_appointments_patient_id ON appointments(patient_id);
CREATE INDEX idx_appointments_appointment_time ON appointments(appointment_time);
CREATE INDEX idx_messages_patient_id ON messages(patient_id);
CREATE INDEX idx_messages_session_id ON messages(session_id);

-- Initial data for agents
INSERT INTO agents (name, role) VALUES
('coordinator', 'Handles incoming messages and routes them to the appropriate agent.'),
('scheduler', 'Manages booking, rescheduling, and canceling appointments.'),
('faq_agent', 'Answers frequently asked questions about the clinic and services.');

-- Function to update 'updated_at' timestamp
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for appointments table
CREATE TRIGGER set_timestamp
BEFORE UPDATE ON appointments
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

-- Comments for clarity
COMMENT ON TABLE patients IS 'Stores essential information about patients communicating with the system.';
COMMENT ON TABLE appointments IS 'Manages all appointment data, linking patients to scheduled times.';
COMMENT ON TABLE agents IS 'Defines the different AI agents and their roles within the system.';
COMMENT ON TABLE messages IS 'A complete log of all communications for auditing, debugging, and future training.';
COMMENT ON COLUMN patients.phone_number IS 'The primary unique identifier for a patient, used for WhatsApp communication.';
COMMENT ON COLUMN appointments.status IS 'The current state of the appointment (scheduled, completed, canceled).';
COMMENT ON COLUMN messages.sender IS 'Indicates whether the message was sent by the patient or an AI agent.';

COMMIT;
