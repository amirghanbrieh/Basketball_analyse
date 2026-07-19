class NBAReceiverQuaries:
    
    query_agility = """
        SELECT
            s.season_years,
            IF(s.season_years < '2022-2023', 'past_period', 'recent_period') AS period_group,
            p.id AS player_id,
            p.fullname,
            p.height / NULLIF(p.weight, 0) AS agility
        FROM awards a
        JOIN season_player sp ON a.season_player_id = sp.id
        JOIN players p ON sp.player_id = p.id
        JOIN season s ON sp.season_id = s.id
        WHERE a.name REGEXP '^MVP-[0-9]+$'
          AND s.season_years BETWEEN '2020-2021' AND '2023-2024'
          AND p.height IS NOT NULL
          AND p.weight IS NOT NULL;

        """

    
    query_intrinsic = """
        WITH champs AS (
            SELECT
                s.season_years,
                CAST(SUBSTRING(s.season_years, 1, 4) AS SIGNED) AS season_start_year,
                c.name AS champion_club,
                p.id AS player_id,
                p.fullname,
                p.born_year,
                p.from_year
            FROM season_club sc
            JOIN season s ON sc.season_id = s.id
            JOIN clubs c ON sc.club_id = c.id
            JOIN player_season_club psc
                ON psc.season_id = sc.season_id
            AND psc.club_id = sc.club_id
            JOIN players p ON psc.player_id = p.id
            WHERE sc.rank = 1
            AND p.is_active = 1
            AND s.season_years IN ('2020-2021', '2021-2022', '2022-2023', '2023-2024')
        )
        SELECT DISTINCT
            season_years,
            CASE WHEN season_years IN ('2020-2021', '2021-2022')
                THEN 'past_period'
                ELSE 'recent_period'
            END AS period_group,
            champion_club,
            player_id,
            fullname,
            season_start_year - born_year AS age,
            season_start_year - from_year + 1  AS experience,
            CAST(season_start_year - from_year + 1 AS DECIMAL(10,4))
                / NULLIF(season_start_year - born_year, 0) AS intrinsic_talent
        FROM champs
        WHERE season_start_year >= from_year
        AND season_start_year >= born_year;

        """
