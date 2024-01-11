BEGIN;
CREATE TABLE IF NOT EXISTS branches(
    id PRIMARY KEY,
    name
);
CREATE TABLE IF NOT EXISTS discord_users(
    id PRIMARY KEY, 
    username, 
    nickname,
    branch_id,
    FOREIGN KEY(branch_id) REFERENCES branches(id)
);
CREATE TABLE IF NOT EXISTS aquatic_directors(
    id PRIMARY KEY,
    discord_id UNIQUE,
    branch_id UNIQUE,
    FOREIGN KEY(discord_id) REFERENCES discord_users(id),
    FOREIGN KEY(branch_id) REFERENCES branches(id)
);
CREATE TABLE IF NOT EXISTS aquatic_specialists(
    id PRIMARY KEY,
    discord_id UNIQUE,
    branch_id UNIQUE,
    FOREIGN KEY(discord_id) REFERENCES discord_users(id),
    FOREIGN KEY(branch_id) REFERENCES branches(id)
);
CREATE TABLE IF NOT EXISTS w2w_users(
    id PRIMARY KEY,
    discord_id UNIQUE,
    first_name,
    last_name,
    branch_id,
    email,
    cert_expiration_date,
    FOREIGN KEY(discord_id) REFERENCES discord_users(id),
    FOREIGN KEY(branch_id) REFERENCES branches(id)
);
CREATE TABLE IF NOT EXISTS pectora_users(
    id PRIMARY KEY,
    discord_id UNIQUE,
    first_name,
    last_name,
    branch_id,
    email,
    cert_expiration_date,
    FOREIGN KEY(discord_id) REFERENCES discord_users(id),
    FOREIGN KEY(branch_id) REFERENCES branches(id)
);
CREATE TABLE IF NOT EXISTS chem_checks(
    chem_uuid PRIMARY KEY,
    discord_id,
    name,
    branch_id,
    pool,
    sample_location,
    sample_time,
    submit_time, 
    chlorine,
    ph,
    water_temp,
    num_of_swimmers,
    FOREIGN KEY(discord_id) REFERENCES discord_users(id),
    FOREIGN KEY(branch_id) REFERENCES branches(id)
);
CREATE TABLE IF NOT EXISTS vats(
    vat_uuid PRIMARY KEY,
    guard_discord_id,
    guard_name,
    sup_discord_id,
    sup_name,
    branch_id,
    pool,
    vat_time,
    submit_time,
    num_of_swimmers,
    num_of_guards,
    stimuli,
    depth,
    pass,
    response_time,
    FOREIGN KEY(guard_discord_id) REFERENCES discord_users(id),
    FOREIGN KEY(sup_discord_id) REFERENCES discord_users(id),
    FOREIGN KEY(branch_id) REFERENCES branches(id)
);
CREATE TABLE IF NOT EXISTS opening_checklists(
    oc_uuid PRIMARY KEY,
    discord_id,
    name,
    branch_id,
    pool,
    opening_time,
    submit_time,
    regulatory_info,
    aed_info,
    adult_pads_expiration_date,
    pediatric_pads_expiration_date,
    aspirin_expiration_date,
    sup_oxygen_info,
    sup_oxygen_psi,
    first_aid_info,
    chlorine,
    ph,
    water_temp,
    lights_function,
    handicap_chair_function,
    spare_battery_present,
    vacuum_present,
    FOREIGN KEY(discord_id) REFERENCES discord_users(id),
    FOREIGN KEY(branch_id) REFERENCES branches(id)
);
CREATE TABLE IF NOT EXISTS closing_checklists(
    oc_uuid PRIMARY KEY,
    discord_id,
    name,
    branch_id,
    pool,
    closing_time,
    submit_time,
    regulatory_info,
    chlorine,
    ph,
    water_temp,
    lights_function,
    vacuum_function,
    FOREIGN KEY(discord_id) REFERENCES discord_users(id),
    FOREIGN KEY(branch_id) REFERENCES branches(id)
);
COMMIT;