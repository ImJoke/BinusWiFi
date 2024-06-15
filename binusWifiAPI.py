from quart import Quart, request, jsonify
import aiosqlite
import os

app = Quart(__name__)

class WifiAttend:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'attendance.db')

    async def init_db(self):
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS bssids (
                        facilityId TEXT,
                        bssid TEXT NOT NULL,
                        UNIQUE(facilityId, bssid)
                    )
                ''')
                await conn.commit()
        except Exception as e:
            print(f"Error initializing database: {e}")

    async def insert_bssid(self, bssid, facilityId=None):
        if not bssid:
            return {'status': 'error', 'message': 'bssid cannot be None'}, 400
   
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute('BEGIN IMMEDIATE')  # Start a new transaction
                async with conn.execute('''
                    SELECT facilityId FROM bssids WHERE bssid = ?
                ''', (bssid,)) as cursor:
                    existing_entry = await cursor.fetchone()

                if existing_entry:
                    if facilityId is None:
                        await conn.rollback()
                        return {'status': 'error', 'message': 'BSSID already exists'}, 409
                    elif existing_entry[0]:
                        await conn.rollback()
                        return {'status': 'error', 'message': 'BSSID and facilityId pair already exists'}, 409
                    else:
                        await conn.execute('''
                            UPDATE bssids SET facilityId = ? WHERE bssid = ?
                        ''', (facilityId, bssid))
                        await conn.commit()
                        return {'status': 'success', 'message': 'BSSID updated with new facilityId'}, 200
                else:
                    if facilityId is None:
                        await conn.execute('''
                            INSERT INTO bssids (facilityId, bssid) VALUES (NULL, ?)
                        ''', (bssid,))
                    else:
                        await conn.execute('''
                            INSERT INTO bssids (facilityId, bssid) VALUES (?, ?)
                        ''', (facilityId, bssid))
                    await conn.commit()
                    return {'status': 'success', 'message': 'BSSID inserted'}, 201
        except Exception as e:
            await conn.rollback()  # Ensure rollback on any exception
            return {'status': 'error', 'message': f"Error inserting BSSID: {e}"}, 500

    async def get_all_bssids(self):
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                async with conn.execute('SELECT facilityId, bssid FROM bssids') as cursor:
                    rows = await cursor.fetchall()
                    result = {}
                    for row in rows:
                        facilityId = row[0] if row[0] else "None"
                        bssid = row[1]
                        if facilityId not in result:
                            result[facilityId] = set()
                        result[facilityId].add(bssid)
                    # Convert sets to lists for JSON serialization
                    return {'status': 'success', 'message': {k: list(v) for k, v in result.items()}}, 200
        except Exception as e:
            print(f"Error retrieving all BSSIDs: {e}")
            return {'status': 'error', 'message': f"Error retrieving all BSSIDs: {e}"}, 500

    async def get_bssids_by_facility(self, facilityId):
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                async with conn.execute('SELECT bssid FROM bssids WHERE facilityId = ?', (facilityId,)) as cursor:
                    rows = await cursor.fetchall()
                    return {'status': 'success', 'message': [row[0] for row in rows]}, 200
        except Exception as e:
            print(f"Error retrieving BSSIDs by facilityId: {e}")
            return {'status': 'error', 'message': f"Error retrieving BSSIDs by facilityId: {e}"}, 500

    async def delete_bssid(self, bssid, facilityId=None):
        if not bssid:
            return {'status': 'error', 'message': 'bssid is required'}, 400

        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute('BEGIN IMMEDIATE')
                async with conn.execute('''
                    SELECT 1 FROM bssids WHERE bssid = ? AND (facilityId = ? OR ? IS NULL)
                ''', (bssid, facilityId, facilityId)) as cursor:
                    existing_entry = await cursor.fetchone()

                if not existing_entry:
                    await conn.rollback()
                    return {'status': 'error', 'message': 'BSSID not found'}, 404

                await conn.execute('''
                    DELETE FROM bssids WHERE bssid = ? AND (facilityId = ? OR ? IS NULL)
                ''', (bssid, facilityId, facilityId))
                await conn.commit()
                return {'status': 'success', 'message': 'BSSID deleted'}, 200
        except Exception as e:
            await conn.rollback()  # Ensure rollback on any exception
            return {'status': 'error', 'message': f"Error deleting BSSID: {e}"}, 500

    async def delete_facility(self, facilityId):
        if not facilityId:
            return {'status': 'error', 'message': 'facilityId is required'}, 400

        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute('BEGIN IMMEDIATE')
                async with conn.execute('''
                    SELECT 1 FROM bssids WHERE facilityId = ?
                ''', (facilityId,)) as cursor:
                    existing_entry = await cursor.fetchone()

                if not existing_entry:
                    await conn.rollback()
                    return {'status': 'error', 'message': 'FacilityId not found'}, 404

                await conn.execute('''
                    DELETE FROM bssids WHERE facilityId = ?
                ''', (facilityId,))
                await conn.commit()
                return {'status': 'success', 'message': 'Facility and its BSSIDs deleted'}, 200
        except Exception as e:
            await conn.rollback()  # Ensure rollback on any exception
            return {'status': 'error', 'message': f"Error deleting facility: {e}"}, 500

    async def delete_database(self):
        try:
            if not os.path.exists(self.db_path):
                return {'status': 'error', 'message': 'Database not found'}, 404

            os.remove(self.db_path)
            return {'status': 'success', 'message': 'Database deleted'}, 200
        except Exception as e:
            return {'status': 'error', 'message': f"Error deleting database: {e}"}, 500


@app.route('/api/insert_bssid', methods=['POST'])
async def insert_bssid():
    try:
        data = await request.json
        bssid = data.get('bssid')
        facilityId = data.get('facilityId', None)

        wifi_attend = WifiAttend()
        await wifi_attend.init_db()
        result, status_code = await wifi_attend.insert_bssid(bssid, facilityId)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error processing request: {e}"}), 500

@app.route('/api/get_bssids/<facilityId>', methods=['GET'])
async def get_bssids_by_facility(facilityId):
    try:
        wifi_attend = WifiAttend()
        await wifi_attend.init_db()
        result, status_code = await wifi_attend.get_bssids_by_facility(facilityId)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error processing request: {e}"}), 500

@app.route('/api/get_bssids', methods=['GET'])
async def get_bssids():
    try:
        wifi_attend = WifiAttend()
        await wifi_attend.init_db()
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

        wifi_attend = WifiAttend()
        await wifi_attend.init_db()
        result, status_code = await wifi_attend.delete_bssid(bssid, facilityId)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error processing request: {e}"}), 500

@app.route('/api/delete_facility', methods=['DELETE'])
async def delete_facility():
    try:
        data = await request.json
        facilityId = data.get('facilityId')

        wifi_attend = WifiAttend()
        await wifi_attend.init_db()
        result, status_code = await wifi_attend.delete_facility(facilityId)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error processing request: {e}"}), 500

@app.route('/api/delete_database', methods=['DELETE'])
async def delete_database():
    try:
        wifi_attend = WifiAttend()
        result, status_code = await wifi_attend.delete_database()
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error processing request: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
