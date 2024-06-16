from quart import Quart, request, jsonify
import asyncpg
import asyncio
import os

app = Quart(__name__)

class WifiAttend:
    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def init_db(self):
        async with self.db_pool.acquire() as conn:
            try:
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS bssids (
                        facilityId TEXT,
                        bssid TEXT NOT NULL,
                        UNIQUE(facilityId, bssid)
                    )
                ''')
            except Exception as e:
                print(f"Error initializing database: {e}")

    async def check_and_init_db(self):
        async with self.db_pool.acquire() as conn:
            try:
                table_exists = await conn.fetchval('''
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        AND table_name = 'bssids'
                    )
                ''')
                if not table_exists:
                    await self.init_db()
            except Exception as e:
                print(f"Error checking database: {e}")

    async def insert_bssid(self, bssid, facilityId=None):
        if not bssid:
            return {'status': 'error', 'message': 'bssid cannot be None'}, 400

        await self.check_and_init_db()
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                existing_entry = await conn.fetchrow('SELECT facilityId FROM bssids WHERE bssid = $1', bssid)

                if existing_entry:
                    if facilityId is None:
                        return {'status': 'error', 'message': 'BSSID already exists'}, 409
                    elif existing_entry['facilityid']:
                        return {'status': 'error', 'message': 'BSSID and facilityId pair already exists'}, 409
                    else:
                        await conn.execute('UPDATE bssids SET facilityId = $1 WHERE bssid = $2', facilityId, bssid)
                        return {'status': 'success', 'message': 'BSSID updated with new facilityId'}, 200
                else:
                    if facilityId is None:
                        await conn.execute('INSERT INTO bssids (facilityId, bssid) VALUES (NULL, $1)', bssid)
                    else:
                        await conn.execute('INSERT INTO bssids (facilityId, bssid) VALUES ($1, $2)', facilityId, bssid)
                    return {'status': 'success', 'message': 'BSSID inserted'}, 201

    async def get_all_bssids(self):
        await self.check_and_init_db()
        
        async with self.db_pool.acquire() as conn:
            try:
                rows = await conn.fetch('SELECT facilityId, bssid FROM bssids')

                result = {}
                for row in rows:
                    facilityId = row['facilityid'] if row['facilityid'] else "None"
                    bssid = row['bssid']
                    if facilityId not in result:
                        result[facilityId] = set()
                    result[facilityId].add(bssid)

                message = {k: list(v) for k, v in result.items()}
                return {'status': 'success', 'message': message}, 200
            except Exception as e:
                print(f"Error retrieving all BSSIDs: {e}")
                return {'status': 'error', 'message': f"Error retrieving all BSSIDs: {e}"}, 500

    async def get_bssids_by_facility(self, facilityId):
        await self.check_and_init_db()
        
        async with self.db_pool.acquire() as conn:
            try:
                rows = await conn.fetch('SELECT bssid FROM bssids WHERE facilityId = $1', facilityId)
                bssids = [row['bssid'] for row in rows]
                return {'status': 'success', 'message': bssids}, 200
            except Exception as e:
                print(f"Error retrieving BSSIDs by facilityId: {e}")
                return {'status': 'error', 'message': f"Error retrieving BSSIDs by facilityId: {e}"}, 500

    async def delete_bssid(self, bssid, facilityId=None):
        if not bssid:
            return {'status': 'error', 'message': 'bssid is required'}, 400

        await self.check_and_init_db()
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                existing_entry = await conn.fetchrow('''
                    SELECT 1 FROM bssids WHERE bssid = $1 AND (facilityId = $2 OR $2 IS NULL)
                ''', bssid, facilityId)

                if not existing_entry:
                    return {'status': 'error', 'message': 'BSSID not found'}, 404

                await conn.execute('''
                    DELETE FROM bssids WHERE bssid = $1 AND (facilityId = $2 OR $2 IS NULL)
                ''', bssid, facilityId)
                return {'status': 'success', 'message': 'BSSID deleted'}, 200

    async def delete_facility(self, facilityId):
        if not facilityId:
            return {'status': 'error', 'message': 'facilityId is required'}, 400

        await self.check_and_init_db()
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                existing_entry = await conn.fetchrow('SELECT 1 FROM bssids WHERE facilityId = $1', facilityId)

                if not existing_entry:
                    return {'status': 'error', 'message': 'FacilityId not found'}, 404

                await conn.execute('DELETE FROM bssids WHERE facilityId = $1', facilityId)
                return {'status': 'success', 'message': 'Facility and its BSSIDs deleted'}, 200

    async def delete_database(self):
        async with self.db_pool.acquire() as conn:
            # Check if the table exists
            table_exists = await conn.fetchval('''
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    AND table_name = 'bssids'
                )
            ''')
            if not table_exists:
                return {'status': 'error', 'message': 'Database not found'}, 404

            await conn.execute('DROP TABLE IF EXISTS bssids')
            return {'status': 'success', 'message': 'Database deleted'}, 200


async def get_db_pool():
    db_url = os.getenv('POSTGRES_URL')
    return await asyncpg.create_pool(dsn=db_url)

@app.before_serving
async def setup_db():
    app.db_pool = await get_db_pool()
    wifi_attend = WifiAttend(app.db_pool)
    await wifi_attend.init_db()


@app.route('/api/insert_bssid', methods=['POST'])
async def insert_bssid():
    try:
        data = await request.json
        bssid = data.get('bssid')
        facilityId = data.get('facilityId', None)

        wifi_attend = WifiAttend(app.db_pool)
        result, status_code = await wifi_attend.insert_bssid(bssid, facilityId)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error processing request: {e}"}), 500

@app.route('/api/get_bssids/<facilityId>', methods=['GET'])
async def get_bssids_by_facility(facilityId):
    try:
        wifi_attend = WifiAttend(app.db_pool)
        result, status_code = await wifi_attend.get_bssids_by_facility(facilityId)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error processing request: {e}"}), 500

@app.route('/api/get_bssids', methods=['GET'])
async def get_bssids():
    try:
        wifi_attend = WifiAttend(app.db_pool)
        result, status_code = await wifi_attend.get_all_bssids()
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error processing request: {e}"}), 500

@app.route('/api/delete_bssid', methods=['DELETE'])
async def delete_bssid():
    try:
        data = await request.json
        bssid = data.get('bssid')
        facilityId = data.get('facilityId', None)

        wifi_attend = WifiAttend(app.db_pool)
        result, status_code = await wifi_attend.delete_bssid(bssid, facilityId)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error processing request: {e}"}), 500

@app.route('/api/delete_facility', methods=['DELETE'])
async def delete_facility():
    try:
        data = await request.json
        facilityId = data.get('facilityId')

        wifi_attend = WifiAttend(app.db_pool)
        result, status_code = await wifi_attend.delete_facility(facilityId)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error processing request: {e}"}), 500

@app.route('/api/delete_database', methods=['DELETE'])
async def delete_database():
    try:
        wifi_attend = WifiAttend(app.db_pool)
        result, status_code = await wifi_attend.delete_database()
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error processing request: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
