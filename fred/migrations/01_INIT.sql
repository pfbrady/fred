BEGIN;
CREATE TABLE IF NOT EXISTS branches(
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pool_groups(
    id TEXT PRIMARY KEY NOT NULL,
    branch_id TEXT NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY(branch_id) REFERENCES branches(id)
);
CREATE TABLE IF NOT EXISTS pools(
    id TEXT PRIMARY KEY NOT NULL,
    branch_id TEXT NOT NULL,
    pool_group_id TEXT NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY(branch_id) REFERENCES branches(id),
    FOREIGN KEY(pool_group_id) REFERENCES pool_groups(id)
);
CREATE TABLE IF NOT EXISTS discord_users(
    id INT PRIMARY KEY NOT NULL, 
    username TEXT NOT NULL, 
    nickname TEXT NOT NULL,
    branch_id TEXT,
    FOREIGN KEY(branch_id) REFERENCES branches(id)
);
CREATE TABLE IF NOT EXISTS w2w_users(
    id INT PRIMARY KEY NOT NULL,
    discord_id INT UNIQUE,
    first_name TEXT,
    last_name TEXT,
    branch_id TEXT,
    email TEXT,
    cert_expiration_date TEXT,
    FOREIGN KEY(discord_id) REFERENCES discord_users(id),
    FOREIGN KEY(branch_id) REFERENCES branches(id)
);
CREATE TABLE IF NOT EXISTS pectora_users(
    id INT PRIMARY KEY NOT NULL,
    discord_id INT UNIQUE,
    first_name TEXT,
    last_name TEXT,
    branch_id TEXT,
    email TEXT,
    cert_expiration_date TEXT,
    FOREIGN KEY(discord_id) REFERENCES discord_users(id),
    FOREIGN KEY(branch_id) REFERENCES branches(id)
);
CREATE TABLE IF NOT EXISTS chem_checks(
    chem_uuid INT PRIMARY KEY NOT NULL,
    discord_id INT,
    name TEXT,
    branch_id TEXT,
    pool_id TEXT,
    sample_location TEXT,
    sample_time TEXT,
    submit_time TEXT, 
    chlorine REAL,
    ph REAL,
    water_temp INT,
    num_of_swimmers INT,
    FOREIGN KEY(discord_id) REFERENCES discord_users(id),
    FOREIGN KEY(branch_id) REFERENCES branches(id),
    FOREIGN KEY(pool_id) REFERENCES pools(id),
    UNIQUE(discord_id, sample_time, pool_id)
);
CREATE TABLE IF NOT EXISTS vats(
    vat_uuid INT PRIMARY KEY NOT NULL,
    guard_discord_id INT,
    guard_name TEXT,
    sup_discord_id INT,
    sup_name TEXT,
    branch_id TEXT,
    pool_id TEXT,
    vat_time TEXT,
    submit_time TEXT,
    num_of_swimmers INT,
    num_of_guards INT,
    stimuli TEXT,
    depth REAL,
    response_time REAL,
    FOREIGN KEY(guard_discord_id) REFERENCES discord_users(id),
    FOREIGN KEY(sup_discord_id) REFERENCES discord_users(id),
    FOREIGN KEY(branch_id) REFERENCES branches(id),
    FOREIGN KEY(pool_id) REFERENCES pools(id),
    UNIQUE(guard_discord_id, sup_discord_id, vat_time)
);
CREATE TABLE IF NOT EXISTS opening_checklists(
    oc_uuid INT PRIMARY KEY NOT NULL,
    discord_id INT,
    name TEXT,
    branch_id TEXT,
    checklist_group TEXT,
    opening_time TEXT,
    submit_time TEXT,
    regulatory_info TEXT,
    aed_info TEXT,
    adult_pads_expiration_date TEXT,
    pediatric_pads_expiration_date TEXT,
    aspirin_expiration_date TEXT,
    sup_oxygen_info TEXT,
    sup_oxygen_psi INT,
    first_aid_info TEXT,
    chlorine REAL,
    ph REAL,
    water_temp INT,
    lights_function TEXT,
    handicap_chair_function TEXT,
    spare_battery_present TEXT,
    vacuum_present TEXT,
    FOREIGN KEY(discord_id) REFERENCES discord_users(id),
    FOREIGN KEY(branch_id) REFERENCES branches(id),
    UNIQUE(discord_id, checklist_group, opening_time)
);
CREATE TABLE IF NOT EXISTS closing_checklists(
    oc_uuid INT PRIMARY KEY NOT NULL,
    discord_id INT,
    name TEXT,
    branch_id TEXT,
    checklist_group TEXT,
    closing_time TEXT,
    submit_time TEXT,
    regulatory_info TEXT,
    chlorine REAL,
    ph REAL,
    water_temp INT,
    lights_function TEXT,
    vacuum_function TEXT,
    FOREIGN KEY(discord_id) REFERENCES discord_users(id),
    FOREIGN KEY(branch_id) REFERENCES branches(id),
    UNIQUE(discord_id, checklist_group, closing_time)
);
COMMIT;