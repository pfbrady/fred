CREATE VIEW test_view AS
SELECT discord_users.id, discord_users.nickname, vats_sup_total.vat_total
FROM
(SELECT sup_discord_id, COUNT(sup_discord_id) AS vat_total
FROM vats
WHERE sup_discord_id IS NOT NULL
GROUP BY sup_discord_id) AS vats_sup_total
LEFT JOIN discord_users
ON discord_users.id = vats_sup_total.sup_discord_id;