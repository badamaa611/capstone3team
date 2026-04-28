-- Хэрэглэгч (багш + сурагч)
CREATE TABLE IF NOT EXISTS users (
    id        SERIAL PRIMARY KEY,
    ner       VARCHAR(100) NOT NULL,
    email     VARCHAR(150) UNIQUE NOT NULL,
    nuuts_ug  VARCHAR(255) NOT NULL,
    duwer     VARCHAR(10)  NOT NULL DEFAULT 'suragch', -- 'bagsh' | 'suragch'
    angi      VARCHAR(5),
    created   TIMESTAMP DEFAULT NOW()
);

-- Асуултын сан
CREATE TABLE IF NOT EXISTS questions (
    id             SERIAL PRIMARY KEY,
    angi           VARCHAR(5)   NOT NULL,  -- '5','9','12'
    hicheel        VARCHAR(50)  NOT NULL,
    sedew          VARCHAR(200) NOT NULL,
    blueprint_kod  VARCHAR(20),
    asuult         TEXT         NOT NULL,
    a_hariu        TEXT,
    b_hariu        TEXT,
    v_hariu        TEXT,
    g_hariu        TEXT,
    d_hariu        TEXT,
    zow_hariult    VARCHAR(1)   NOT NULL,  -- 'A','B','V','G','D'
    tuwshin        SMALLINT     NOT NULL,  -- 1=Мэдлэг 2=Чадвар 3=Хэрэглээ
    created        TIMESTAMP DEFAULT NOW()
);

-- Тестийн сесс
CREATE TABLE IF NOT EXISTS test_sessions (
    id           SERIAL PRIMARY KEY,
    suragch_id   INT REFERENCES users(id),
    angi         VARCHAR(5),
    hicheel      VARCHAR(50),
    egneliin_tsag TIMESTAMP DEFAULT NOW(),
    duusah_tsag  TIMESTAMP,
    niit_onoo    INT DEFAULT 0,
    too          INT DEFAULT 0
);

-- Тестийн хариулт
CREATE TABLE IF NOT EXISTS test_answers (
    id          SERIAL PRIMARY KEY,
    session_id  INT REFERENCES test_sessions(id),
    question_id INT REFERENCES questions(id),
    ogson_hariult VARCHAR(1),
    zuw_esehuu  BOOLEAN,
    ai_asuu     BOOLEAN DEFAULT FALSE  -- AI нэмэлт асуулт мөн эсэх
);

-- Сурагчийн сул сэдвүүд
CREATE TABLE IF NOT EXISTS weak_topics (
    id          SERIAL PRIMARY KEY,
    suragch_id  INT REFERENCES users(id),
    hicheel     VARCHAR(50),
    sedew       VARCHAR(200),
    aldaa_too   INT DEFAULT 1,
    updated     TIMESTAMP DEFAULT NOW()
);
