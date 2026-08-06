def get_money_income(cursor, nation_id):

    cursor.execute("""
        SELECT
            capital_count,
            city_count
        FROM nations
        WHERE nation_id = %s
    """, (nation_id,))

    nation = cursor.fetchone()

    return (
        nation["capital_count"] * 200000000 +
        nation["city_count"] * 50000000
    )

def get_money_upkeep(cursor, nation_id):

    # -------------------------
    # Building Upkeep
    # -------------------------

    cursor.execute("""
        SELECT
            SUM(nb.quantity * b.money_upkeep) AS total

        FROM nation_buildings nb

        JOIN buildings b
            ON nb.building_id = b.building_id

        WHERE nb.nation_id = %s
    """, (nation_id,))

    building = cursor.fetchone()["total"] or 0

    # -------------------------
    # Unit Upkeep
    # -------------------------

    cursor.execute("""
        SELECT
            SUM(u.money_upkeep * nu.tier_level) AS total

        FROM nation_units nu

        JOIN units u
            ON nu.unit_id = u.unit_id

        WHERE
            nu.nation_id = %s
        AND
            nu.status = 'active'
    """, (nation_id,))

    unit = cursor.fetchone()["total"] or 0

    return building + unit


def get_oil_production(cursor, nation_id):

    cursor.execute("""
        SELECT
            SUM(nb.quantity * bro.per_turn_amount) AS total

        FROM nation_buildings nb

        JOIN building_resource_outputs bro
            ON nb.building_id = bro.building_id
            AND nb.resource_id = bro.resource_id

        WHERE
            nb.nation_id = %s
        AND
            bro.resource_id = 4
    """, (nation_id,))

    result = cursor.fetchone()["total"]

    return result or 0

def get_oil_consumption(cursor, nation_id):

    cursor.execute("""
        SELECT
            SUM(u.oil_upkeep * nu.tier_level) AS total

        FROM nation_units nu

        JOIN units u
            ON nu.unit_id = u.unit_id

        WHERE
            nu.nation_id = %s
        AND
            nu.status = 'active'
    """, (nation_id,))

    result = cursor.fetchone()["total"]

    return result or 0


def get_cm_production(cursor, nation_id):

    cursor.execute("""
        SELECT
            SUM(nb.quantity * bro.per_turn_amount) AS total

        FROM nation_buildings nb

        JOIN building_resource_outputs bro
            ON nb.building_id = bro.building_id
            AND nb.resource_id = bro.resource_id

        WHERE
            nb.nation_id = %s
        AND
            bro.resource_id = 2
    """, (nation_id,))

    result = cursor.fetchone()["total"]

    return result or 0

def get_cm_consumption(cursor, nation_id):

    return 0

def get_rm_production(cursor, nation_id):

    cursor.execute("""
        SELECT
            SUM(nb.quantity * bro.per_turn_amount) AS total

        FROM nation_buildings nb

        JOIN building_resource_outputs bro
            ON nb.building_id = bro.building_id
            AND nb.resource_id = bro.resource_id

        WHERE
            nb.nation_id = %s
        AND
            bro.resource_id = 3
    """, (nation_id,))

    result = cursor.fetchone()["total"]

    return result or 0

def get_rm_consumption(cursor, nation_id):

    return 0