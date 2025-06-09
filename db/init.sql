-- Таблица пользователей
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100) UNIQUE,
    tg_id VARCHAR(50) UNIQUE,
    birth_date DATE,
    registration_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Таблица специализаций
CREATE TABLE Specializations (
    specialization_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- Таблица симптомов
CREATE TABLE Symptoms (
    symptom_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- Таблица врачей
CREATE TABLE Doctors (
    doctor_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    specialization_id INTEGER REFERENCES Specializations(specialization_id),
    phone VARCHAR(20),
    email VARCHAR(100) UNIQUE,
    description TEXT
);

-- Диагностические метки
CREATE TABLE DiagnosticLabels (
    label_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    specialization_id INTEGER REFERENCES Specializations(specialization_id),
    description TEXT
);

-- Связь симптомов и специализаций
CREATE TABLE Symptom_Specialization (
    id SERIAL PRIMARY KEY,
    symptom_id INTEGER REFERENCES Symptoms(symptom_id),
    specialization_id INTEGER REFERENCES Specializations(specialization_id),
    priority INTEGER NOT NULL DEFAULT 1,
    UNIQUE(symptom_id, specialization_id)
);

-- Таблица записей на прием
CREATE TABLE Appointments (
    appointment_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES Users(user_id),
    doctor_id INTEGER REFERENCES Doctors(doctor_id),
    appointment_date TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'confirmed', 'canceled', 'completed')),
    notes TEXT
);

-- Таблица отзывов
CREATE TABLE Reviews (
    review_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES Users(user_id),
    doctor_id INTEGER REFERENCES Doctors(doctor_id),
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Медицинские советы
CREATE TABLE MedicalTips (
    tip_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Медицинские справки
CREATE TABLE Certificates (
    certificate_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES Users(user_id),
    doctor_id INTEGER REFERENCES Doctors(doctor_id),
    issue_date DATE NOT NULL,
    type VARCHAR(100) NOT NULL,
    content TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'expired', 'revoked'))
);

-- Налоговые документы
CREATE TABLE TaxDocuments (
    document_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES Users(user_id),
    issue_date DATE NOT NULL,
    type VARCHAR(100) NOT NULL,
    content TEXT,
    amount DECIMAL(10, 2),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'processed', 'rejected'))
);

-- Наполнение таблицы Specializations
INSERT INTO Specializations (name, description) VALUES
('Гастроэнтерология', 'Диагностика и лечение заболеваний желудочно-кишечного тракта'),
('Гематология', 'Диагностика и лечение заболеваний крови и кроветворных органов'),
('Гинеколог-хирург', 'Хирургическое лечение гинекологических заболеваний'),
('Гинекология', 'Диагностика и лечение заболеваний женской репродуктивной системы'),
('Гинекология-онкология', 'Диагностика и лечение онкологических заболеваний женской репродуктивной системы'),
('Дерматовенерология', 'Диагностика и лечение кожных и венерических заболеваний'),
('Детский гинеколог', 'Диагностика и лечение гинекологических заболеваний у детей и подростков'),
('Кардиология', 'Диагностика и лечение заболеваний сердечно-сосудистой системы'),
('Маммология', 'Диагностика и лечение заболеваний молочных желез'),
('Неврология', 'Диагностика и лечение заболеваний нервной системы'),
('Нутрициология', 'Наука о питании и пищевых продуктах, их влиянии на организм'),
('Онкология', 'Диагностика и лечение злокачественных и доброкачественных опухолей'),
('Отоларингология', 'Диагностика и лечение заболеваний уха, горла и носа (ЛОР)'),
('Офтальмология', 'Диагностика и лечение заболеваний глаз'),
('Педиатрия', 'Медицинское обслуживание детей от рождения до совершеннолетия'),
('Проктология', 'Диагностика и лечение заболеваний прямой кишки и анальной области'),
('Психология', 'Диагностика и коррекция психических состояний и поведения'),
('Психотерапия', 'Лечение психических расстройств психологическими методами'),
('Репродуктология', 'Диагностика и лечение нарушений репродуктивной функции'),
('Рефлексотерапевт', 'Лечение методом воздействия на биологически активные точки'),
('Сосудистая хирургия', 'Хирургическое лечение заболеваний кровеносных сосудов'),
('Терапия', 'Диагностика и лечение внутренних заболеваний'),
('УЗИ', 'Проведение ультразвуковых исследований и диагностика'),
('УЗИ сердца', 'Специализированные ультразвуковые исследования сердца'),
('Урология', 'Диагностика и лечение заболеваний мочеполовой системы'),
('Физиотерапия', 'Лечение с помощью физических факторов (токи, ультразвук и др.)'),
('Хирургия', 'Хирургическое лечение различных заболеваний'),
('Эндокринология', 'Диагностика и лечение заболеваний эндокринной системы');
