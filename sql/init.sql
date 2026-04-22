-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable pgroonga
CREATE EXTENSION IF NOT EXISTS pgroonga;

-- Verify the installation of extensions
SELECT extname
FROM pg_extension
WHERE extname IN ('vector', 'pgroonga');