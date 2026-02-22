-- Создание таблицы заметок (если не существует)
CREATE TABLE IF NOT EXISTS notes (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Добавление тестовых заметок
INSERT INTO notes (text) VALUES 
    ('Первая тестовая заметка'),
    ('Вторая тестовая заметка'),
    ('PostgreSQL работает отлично!')
ON CONFLICT DO NOTHING;