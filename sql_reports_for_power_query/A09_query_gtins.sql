-- Отчет A09: Выборка всех колонок для списка GTIN (до 5 строк на каждый)
-- Использование: вставить список GTIN в ARRAY[] и выполнить
WITH gtin_list AS (
    SELECT unnest(ARRAY[
        '35411183067944',
        '35411183134707',
        '4680934980768',
        '5411183164994',
        '4680934980744',
        '4680934980737',
        '4680934980720',
        '4680934980652',
        '4680934980706',
        '4629670018571',
        '4629670018588',
        '4629670018595',
        '4629670018601',
        '4601745004726',
        '4680934980690',
        '35411183188984',
        '5411183188983',
        '4680934980751',
        '4629670018540'
    ]) AS gtin
),
ranked AS (
    SELECT
        c.*,
        ROW_NUMBER() OVER (
            PARTITION BY c.gtin ORDER BY c.emission_date NULLS LAST
        ) AS rn
    FROM gtin_list g
    JOIN chz_cises c ON c.gtin = g.gtin
)
SELECT
    cis,
    cis_print_view,
    gtin,
    serial_number,
    status,
    status_ext,
    elimination_reason,
    gray_zone,
    emission_date,
    introduced_date,
    application_date,
    production_date,
    introduce_production_date,
    expire_date,
    declaration_date,
    owner_inn,
    producer_inn,
    manufacturer_inn,
    importer_inn,
    product_group,
    package_type,
    package_type_ext,
    general_package_type,
    aggregation_type,
    emission_type,
    tn_ved10,
    country,
    order_id,
    orid,
    mod_id,
    declaration_id,
    declaration_registration_number,
    fts_decision_code,
    paid,
    tracking,
    childs,
    childs_print_view,
    prev_cises,
    next_cises,
    permit_docs,
    licences,
    expiration,
    production_line_id,
    details,
    additional_info,
    raw_extra,
    synced_at,
    sync_mode
FROM ranked
WHERE rn <= 5
ORDER BY gtin, rn;
