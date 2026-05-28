import asyncpg
import config

class Database:
    def __init__(self):
        self.pool = None

    # connects with the database
    async def connect(self):
        try:
            # since we have no Authentication, we can just use the URL
            self.pool = await asyncpg.create_pool(config.DATABASE_URL, ssl=True, min_size=1, max_size=15)

            # gets the database connection from pool
            async with self.pool.acquire() as conn:
                # setting the correct schema
                await conn.execute("CREATE SCHEMA IF NOT EXISTS public")
                await conn.execute("SET search_path TO public")

            print("✅Connected to the database.")

            await self.create_tables()
        except Exception as error:
            print(f"❌Failed to connect to the database: {error}")

    # creates the tables
    async def create_tables(self):
        try:
            # gets the database connection from pool
            async with self.pool.acquire() as conn:
                # creating a table for dynamic variables
                await conn.execute(
                    """
                    -- creating a table called 'VAR' if not exists
                    CREATE TABLE IF NOT EXISTS VAR (
                        -- PRIMARY KEY ensures that the variable_name is unique
                        variable_name VARCHAR(100) PRIMARY KEY,
                        variable_value TEXT,
                        created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'Asia/Dhaka'),
                        updated_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'Asia/Dhaka')
                    );
                """
                )

                # creating a table for logging the data
                await conn.execute(
                    """
                    -- creating a table called 'LOG' if not exists
                    CREATE TABLE IF NOT EXISTS LOG (
                        opening_time TEXT PRIMARY KEY,
                        closing_time TEXT,
                        was_active_for TEXT
                    );
                """
                )
                print("✅Variables table ready!")
        except Exception as error:
            print(f"❌ Error creating tables: {error}")

    # updating the variables in the database
    async def set_variable(self, name: str, value: str):
        try:
            # gets the database connection from pool
            async with self.pool.acquire() as conn:
                # updating the variable value in the table
                await conn.execute(
                    """
                    -- inserts a new variable in the table
                    INSERT INTO VAR (variable_name, variable_value)
                    -- $1 and $2 are asyncpg placeholders
                    VALUES ($1, $2)
                    -- conflict occurs when the variable_name already exists
                    -- if the variable_name already exists, it updates the variable_value
                    ON CONFLICT (variable_name) DO UPDATE
                    SET variable_value = $2,
                    updated_at = TIMEZONE('Asia/Dhaka', NOW())
                    """,
                    name,
                    str(value),
                )
                print(f"✅ Variable {name} set to {value}")
        except Exception as error:
            print(f"❌ Error setting variable {name}: {error}")

    async def get_variable(self, name: str):
        try:
            # gets the database connection from pool
            async with self.pool.acquire() as conn:
                # getting the variable value from the table
                result = await conn.fetchrow(
                    """
                    -- gets the variable value from the table
                    SELECT variable_value
                    FROM VAR
                    WHERE variable_name = $1
                    """,
                    name,
                )
                # returning the variable value
                return result["variable_value"] if result else None
        except Exception as error:
            print(f"❌ Error getting variable {name}: {error}")
            return None

    async def set_log(self, opening_time: str, closing_time: str, was_active_for: str):
        try:
            # gets the database connection from pool
            async with self.pool.acquire() as conn:
                # adding a new row to the log table
                await conn.execute(
                    """
                    -- tries to insert a new variable in the table
                    INSERT INTO LOG (opening_time, closing_time, was_active_for)
                    -- $1, $2 and $3 are asyncpg placeholders
                    VALUES ($1, $2, $3)
                    -- conflict occurs when the opening_time already exists
                        -- updating the closing_time and was_active_for
                    ON CONFLICT (opening_time) DO UPDATE SET
                        closing_time = $2,
                        was_active_for = $3
                    """,
                    opening_time,
                    closing_time,
                    was_active_for
                )
                print(f"✅ Log set to {opening_time}, {closing_time}, {was_active_for}")
        except Exception as error:
            print(f"❌ Error setting log: {error}")

    async def get_log(self):
        try:
            # gets the database connection from pool
            async with self.pool.acquire() as conn:
                # fetching the last row from the log table
                result = await conn.fetchrow(
                    """
                    -- tries to get the variable value from the table
                    SELECT *
                    FROM LOG
                    ORDER BY opening_time DESC
                    LIMIT 1
                    """,
                )
                # returning the opening_time
                return result["opening_time"] if result else None
        except Exception as error:
            print(f"❌ Error getting last log: {error}")
            return None


db = Database()
