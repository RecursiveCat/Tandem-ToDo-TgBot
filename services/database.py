import asyncpg
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from loguru import logger
from datetime import datetime, date


class AbstractDatabase(ABC):
    @abstractmethod
    async def register_user(self, user_id: int) -> None: pass
    
    @abstractmethod
    async def get_user_info(self, user_id: int) -> Optional[dict]: pass

    @abstractmethod
    async def set_name(self, user_id: int, new_name: str): pass

    @abstractmethod
    async def create_tandem(self, user_id: int, partner_id: int) -> int: pass

    @abstractmethod
    async def get_partner_id(self, user_id: int) -> Optional[int]: pass

    @abstractmethod
    async def get_tandem_info(self, user_id: int) -> Optional[Dict]: pass
    
    @abstractmethod
    async def set_tandem_name(self, tandem_id: int, new_name: str): pass

    @abstractmethod
    async def disband_tandem(self, user_id: int): pass

    @abstractmethod
    async def toggle_task(self, user_id: int, task_id: int) -> bool: pass

    @abstractmethod
    async def get_today_stats(self, user_id: int) -> dict: pass
    
    @abstractmethod
    async def get_tandem_score_breakdown(self, tandem_id: int) -> Dict[int, int]: pass

    @abstractmethod
    async def get_all_users(self, in_tandem: Optional[bool] = None) -> List[int]: pass

    @abstractmethod
    async def get_all_tandems_list(self) -> List[Dict]: pass

    @abstractmethod
    async def get_tandem_summary(self, tandem_id: int) -> Dict: pass

    @abstractmethod
    async def reset_daily_stats(self): pass

    @abstractmethod
    async def create_task(self, title: str, description: str, points: int = 1) -> int: pass

    @abstractmethod
    async def get_all_tasks(self, active_only: bool = True) -> List[Dict]: pass

    @abstractmethod
    async def update_task(self, task_id: int, title: Optional[str] = None, description: Optional[str] = None, points: Optional[int] = None, active: Optional[bool] = None): pass

    @abstractmethod
    async def delete_task(self, task_id: int): pass

    @abstractmethod
    async def get_task(self, task_id: int) -> Optional[Dict]: pass

    @abstractmethod
    async def create_scheduled_challenge(self, task_ids: List[int], send_time: datetime, message_text: Optional[str] = None) -> int: pass

    @abstractmethod
    async def get_pending_scheduled_challenges(self) -> List[Dict]: pass

    @abstractmethod
    async def mark_challenge_sent(self, challenge_id: int): pass

    @abstractmethod
    async def get_pitstop_links(self) -> List[Dict]: pass

    @abstractmethod
    async def add_pitstop_link(self, title: str, url: str) -> int: pass

    @abstractmethod
    async def update_pitstop_link(self, link_id: int, title: Optional[str] = None, url: Optional[str] = None): pass

    @abstractmethod
    async def delete_pitstop_link(self, link_id: int): pass

    @abstractmethod
    async def get_tandem_statistics(self, tandem_id: int, days: int = 7) -> Dict: pass

    @abstractmethod
    async def create_scheduled_message(self, message_type: str, scheduled_time: datetime, target_chat_id: Optional[int] = None, forward_from_message_id: Optional[int] = None, text: Optional[str] = None) -> int: pass

    @abstractmethod
    async def get_pending_scheduled_messages(self) -> List[Dict]: pass

    @abstractmethod
    async def mark_message_sent(self, message_id: int): pass

    @abstractmethod
    async def get_users_with_incomplete_tasks(self, task_ids: List[int]) -> List[Dict]: pass


class PostgresService(AbstractDatabase):
    def __init__(self, dsn: str):
        self.dsn = dsn.replace("postgresql+asyncpg://", "postgresql://")
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        try:
            self._pool = await asyncpg.create_pool(dsn=self.dsn)
            logger.info("Успешное подключение к БД")
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise

    async def disconnect(self):
        if self._pool:
            await self._pool.close()

    async def create_default_tables(self):
        async with self._pool.acquire() as conn:
            await conn.execute('''
            CREATE TABLE IF NOT EXISTS tandems (
                id SERIAL PRIMARY KEY,
                name TEXT DEFAULT 'Тандем',
                created_at TIMESTAMP DEFAULT NOW()
            )
            ''')

            await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                name TEXT DEFAULT 'Безымянный пользователь',
                tandem_id INTEGER REFERENCES tandems(id) ON DELETE SET NULL,
                score INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
            ''')

            await conn.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                last_updated DATE DEFAULT CURRENT_DATE
            )
            ''')

            await conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                points INTEGER DEFAULT 1,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            )
            ''')

            await conn.execute('''
            CREATE TABLE IF NOT EXISTS task_completions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                completed_date DATE DEFAULT CURRENT_DATE,
                UNIQUE(user_id, task_id, completed_date)
            )
            ''')

            await conn.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_challenges (
                id SERIAL PRIMARY KEY,
                task_ids INTEGER[] NOT NULL,
                message_text TEXT,
                send_time TIMESTAMP NOT NULL,
                sent BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
            ''')

            await conn.execute('''
            CREATE TABLE IF NOT EXISTS pitstop_links (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            )
            ''')

            await conn.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_messages (
                id SERIAL PRIMARY KEY,
                message_type TEXT NOT NULL,
                scheduled_time TIMESTAMP NOT NULL,
                target_chat_id BIGINT,
                forward_from_message_id INTEGER,
                text TEXT,
                sent BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
            ''')

            await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_task_completions_user_date 
            ON task_completions(user_id, completed_date)
            ''')

            await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_scheduled_challenges_time 
            ON scheduled_challenges(send_time) WHERE sent = FALSE
            ''')

            await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_scheduled_messages_time 
            ON scheduled_messages(scheduled_time) WHERE sent = FALSE
            ''')

    async def register_user(self, user_id: int):
        async with self._pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO users (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING', 
                user_id
            )
            await conn.execute(
                'INSERT INTO daily_stats (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING', 
                user_id
            )

    async def get_user_info(self, user_id: int) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
            return dict(row) if row else None

    async def set_name(self, user_id: int, new_name: str):
        async with self._pool.acquire() as conn:
            await conn.execute('UPDATE users SET name = $1 WHERE user_id = $2', new_name, user_id)

    async def create_tandem(self, user_id: int, partner_id: int) -> int:
        async with self._pool.acquire() as conn:
            async with conn.transaction(): 
                await conn.execute('INSERT INTO users (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING', user_id)
                await conn.execute('INSERT INTO users (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING', partner_id)
                await conn.execute('INSERT INTO daily_stats (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING', user_id)
                await conn.execute('INSERT INTO daily_stats (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING', partner_id)
                tandem_id = await conn.fetchval('INSERT INTO tandems DEFAULT VALUES RETURNING id')
                await conn.execute('UPDATE users SET tandem_id = $1 WHERE user_id IN ($2, $3)', 
                                   tandem_id, user_id, partner_id)
                return tandem_id

    async def set_tandem_name(self, tandem_id: int, new_name: str):
        async with self._pool.acquire() as conn:
            await conn.execute('UPDATE tandems SET name = $1 WHERE id = $2', new_name, tandem_id)
            
    async def get_partner_id(self, user_id: int) -> Optional[int]:
        async with self._pool.acquire() as conn:
            tandem_id = await conn.fetchval('SELECT tandem_id FROM users WHERE user_id = $1', user_id)
            if not tandem_id:
                return None
            return await conn.fetchval('SELECT user_id FROM users WHERE tandem_id = $1 AND user_id != $2', 
                                         tandem_id, user_id)

    async def get_tandem_info(self, user_id: int) -> Optional[Dict]:
        async with self._pool.acquire() as conn:
            query = """
                SELECT t.id as tandem_id, t.name as tandem_name, 
                        u2.name as partner_name, u2.user_id as partner_id, u1.name as name
                FROM users u1
                JOIN tandems t ON u1.tandem_id = t.id
                JOIN users u2 ON u2.tandem_id = t.id AND u2.user_id != u1.user_id
                WHERE u1.user_id = $1
            """
            row = await conn.fetchrow(query, user_id)
            return dict(row) if row else None

    async def disband_tandem(self, user_id: int):
        async with self._pool.acquire() as conn:
            tandem_id = await conn.fetchval('SELECT tandem_id FROM users WHERE user_id = $1', user_id)
            if tandem_id:
                await conn.execute('DELETE FROM tandems WHERE id = $1', tandem_id)

    async def toggle_task(self, user_id: int, task_id: int) -> bool:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute('INSERT INTO users (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING', user_id)
                await conn.execute('INSERT INTO daily_stats (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING', user_id)
                
                task = await conn.fetchrow('SELECT id, points FROM tasks WHERE id = $1 AND active = TRUE', task_id)
                if not task:
                    logger.warning(f"Попытка переключить несуществующую задачу: {task_id}")
                    return False

                today = date.today()
                existing = await conn.fetchrow(
                    'SELECT id FROM task_completions WHERE user_id = $1 AND task_id = $2 AND completed_date = $3',
                    user_id, task_id, today
                )

                if existing:
                    await conn.execute(
                        'DELETE FROM task_completions WHERE id = $1',
                        existing['id']
                    )
                    await conn.execute(
                        'UPDATE users SET score = GREATEST(score - $1, 0) WHERE user_id = $2',
                        task['points'], user_id
                    )
                    await conn.execute(
                        'UPDATE daily_stats SET last_updated = $1 WHERE user_id = $2',
                        today, user_id
                    )
                    return False
                else:
                    await conn.execute(
                        'INSERT INTO task_completions (user_id, task_id, completed_date) VALUES ($1, $2, $3)',
                        user_id, task_id, today
                    )
                    await conn.execute(
                        'UPDATE users SET score = score + $1 WHERE user_id = $2',
                        task['points'], user_id
                    )
                    await conn.execute(
                        'UPDATE daily_stats SET last_updated = $1 WHERE user_id = $2',
                        today, user_id
                    )
                    return True

    async def get_today_stats(self, user_id: int) -> dict:
        async with self._pool.acquire() as conn:
            await conn.execute('INSERT INTO users (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING', user_id)
            await conn.execute('INSERT INTO daily_stats (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING', user_id)
            
            today = date.today()
            active_tasks = await conn.fetch('SELECT id, title FROM tasks WHERE active = TRUE ORDER BY id')
            completions = await conn.fetch(
                'SELECT task_id FROM task_completions WHERE user_id = $1 AND completed_date = $2',
                user_id, today
            )
            completed_ids = {row['task_id'] for row in completions}
            
            return {str(task['id']): task['id'] in completed_ids for task in active_tasks}

    async def get_tandem_score_breakdown(self, tandem_id: int) -> Dict[int, int]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT user_id, score 
                FROM users 
                WHERE tandem_id = $1
            ''', tandem_id)
            return {row['user_id']: row['score'] for row in rows}

    async def get_all_users(self, in_tandem: Optional[bool] = None) -> List[int]:
        async with self._pool.acquire() as conn:
            query = 'SELECT user_id FROM users'
            conditions = []
            if in_tandem is True:
                conditions.append('tandem_id IS NOT NULL')
            elif in_tandem is False:
                conditions.append('tandem_id IS NULL')
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            rows = await conn.fetch(query)
            return [row['user_id'] for row in rows]

    async def get_all_tandems_list(self) -> List[Dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch('SELECT id, name FROM tandems ORDER BY id')
            return [dict(row) for row in rows]

    async def get_tandem_summary(self, tandem_id: int) -> Dict:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                '''
                SELECT SUM(u.score) AS total_score, array_agg(u.name) AS user_names
                FROM users u
                WHERE u.tandem_id = $1
                ''',
                tandem_id
            )
            if not row or row['total_score'] is None:
                return {'total_score': 0, 'user_names': []}
            return {'total_score': row['total_score'], 'user_names': row['user_names']}

    async def get_all_tandems_with_summary(self) -> List[Dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT 
                    t.id,
                    t.name,
                    COALESCE(SUM(u.score), 0) AS total_score,
                    array_agg(u.name) FILTER (WHERE u.name IS NOT NULL) AS user_names
                FROM tandems t
                LEFT JOIN users u ON u.tandem_id = t.id
                GROUP BY t.id, t.name
                ORDER BY total_score DESC
            ''')
            return [dict(row) for row in rows]

    async def reset_daily_stats(self):
        async with self._pool.acquire() as conn:
            await conn.execute('''
                UPDATE daily_stats 
                SET last_updated = CURRENT_DATE
                WHERE last_updated < CURRENT_DATE
            ''')
            await conn.execute('''
                DELETE FROM task_completions 
                WHERE completed_date < CURRENT_DATE
            ''')
            logger.info("Ежедневная статистика сброшена")

    async def create_task(self, title: str, description: str, points: int = 1) -> int:
        async with self._pool.acquire() as conn:
            task_id = await conn.fetchval(
                'INSERT INTO tasks (title, description, points) VALUES ($1, $2, $3) RETURNING id',
                title, description, points
            )
            return task_id

    async def get_all_tasks(self, active_only: bool = True) -> List[Dict]:
        async with self._pool.acquire() as conn:
            query = 'SELECT id, title, description, points, active, created_at FROM tasks'
            if active_only:
                query += ' WHERE active = TRUE'
            query += ' ORDER BY id'
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    async def update_task(self, task_id: int, title: Optional[str] = None, description: Optional[str] = None, points: Optional[int] = None, active: Optional[bool] = None):
        async with self._pool.acquire() as conn:
            updates = []
            params = []
            param_num = 1
            
            if title is not None:
                updates.append(f'title = ${param_num}')
                params.append(title)
                param_num += 1
            if description is not None:
                updates.append(f'description = ${param_num}')
                params.append(description)
                param_num += 1
            if points is not None:
                updates.append(f'points = ${param_num}')
                params.append(points)
                param_num += 1
            if active is not None:
                updates.append(f'active = ${param_num}')
                params.append(active)
                param_num += 1
            
            if updates:
                params.append(task_id)
                await conn.execute(
                    f'UPDATE tasks SET {", ".join(updates)} WHERE id = ${param_num}',
                    *params
                )

    async def delete_task(self, task_id: int):
        async with self._pool.acquire() as conn:
            await conn.execute('UPDATE tasks SET active = FALSE WHERE id = $1', task_id)

    async def get_task(self, task_id: int) -> Optional[Dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM tasks WHERE id = $1', task_id)
            return dict(row) if row else None

    async def create_scheduled_challenge(self, task_ids: List[int], send_time: datetime, message_text: Optional[str] = None) -> int:
        async with self._pool.acquire() as conn:
            challenge_id = await conn.fetchval(
                'INSERT INTO scheduled_challenges (task_ids, send_time, message_text) VALUES ($1, $2, $3) RETURNING id',
                task_ids, send_time, message_text
            )
            return challenge_id

    async def get_pending_scheduled_challenges(self) -> List[Dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT * FROM scheduled_challenges WHERE sent = FALSE AND send_time <= NOW() ORDER BY send_time'
            )
            return [dict(row) for row in rows]

    async def mark_challenge_sent(self, challenge_id: int):
        async with self._pool.acquire() as conn:
            await conn.execute('UPDATE scheduled_challenges SET sent = TRUE WHERE id = $1', challenge_id)

    async def get_pitstop_links(self, active_only: bool = True) -> List[Dict]:
        async with self._pool.acquire() as conn:
            query = 'SELECT * FROM pitstop_links'
            if active_only:
                query += ' WHERE active = TRUE'
            query += ' ORDER BY id'
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    async def add_pitstop_link(self, title: str, url: str) -> int:
        async with self._pool.acquire() as conn:
            link_id = await conn.fetchval(
                'INSERT INTO pitstop_links (title, url) VALUES ($1, $2) RETURNING id',
                title, url
            )
            return link_id

    async def update_pitstop_link(self, link_id: int, title: Optional[str] = None, url: Optional[str] = None):
        async with self._pool.acquire() as conn:
            updates = []
            params = []
            param_num = 1
            
            if title is not None:
                updates.append(f'title = ${param_num}')
                params.append(title)
                param_num += 1
            if url is not None:
                updates.append(f'url = ${param_num}')
                params.append(url)
                param_num += 1
            
            if updates:
                params.append(link_id)
                await conn.execute(
                    f'UPDATE pitstop_links SET {", ".join(updates)} WHERE id = ${param_num}',
                    *params
                )

    async def delete_pitstop_link(self, link_id: int):
        async with self._pool.acquire() as conn:
            await conn.execute('UPDATE pitstop_links SET active = FALSE WHERE id = $1', link_id)

    async def get_tandem_statistics(self, tandem_id: int, days: int = 7) -> Dict:
        async with self._pool.acquire() as conn:
            user_ids = await conn.fetch(
                'SELECT user_id FROM users WHERE tandem_id = $1',
                tandem_id
            )
            if not user_ids:
                return {'total_score': 0, 'completions_by_day': {}, 'tasks_completed': 0}
            
            user_id_list = [row['user_id'] for row in user_ids]
            
            total_score_row = await conn.fetchrow(
                'SELECT SUM(score) as total FROM users WHERE user_id = ANY($1)',
                user_id_list
            )
            total_score = total_score_row['total'] or 0
            
            completions = await conn.fetch(
                '''
                SELECT 
                    completed_date,
                    COUNT(*) as count
                FROM task_completions
                WHERE user_id = ANY($1) 
                    AND completed_date >= CURRENT_DATE - $2::INTERVAL
                GROUP BY completed_date
                ORDER BY completed_date
                ''',
                user_id_list, f'{days} days'
            )
            
            completions_by_day = {str(row['completed_date']): row['count'] for row in completions}
            
            total_completions = await conn.fetchval(
                '''
                SELECT COUNT(*) 
                FROM task_completions 
                WHERE user_id = ANY($1) 
                    AND completed_date >= CURRENT_DATE - $2::INTERVAL
                ''',
                user_id_list, f'{days} days'
            )
            
            return {
                'total_score': total_score,
                'completions_by_day': completions_by_day,
                'tasks_completed': total_completions or 0
            }

    async def create_scheduled_message(self, message_type: str, scheduled_time: datetime, target_chat_id: Optional[int] = None, forward_from_message_id: Optional[int] = None, text: Optional[str] = None) -> int:
        async with self._pool.acquire() as conn:
            message_id = await conn.fetchval(
                'INSERT INTO scheduled_messages (message_type, scheduled_time, target_chat_id, forward_from_message_id, text) VALUES ($1, $2, $3, $4, $5) RETURNING id',
                message_type, scheduled_time, target_chat_id, forward_from_message_id, text
            )
            return message_id

    async def get_pending_scheduled_messages(self) -> List[Dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT * FROM scheduled_messages WHERE sent = FALSE AND scheduled_time <= NOW() ORDER BY scheduled_time'
            )
            return [dict(row) for row in rows]

    async def mark_message_sent(self, message_id: int):
        async with self._pool.acquire() as conn:
            await conn.execute('UPDATE scheduled_messages SET sent = TRUE WHERE id = $1', message_id)

    async def get_users_with_incomplete_tasks(self, task_ids: List[int]) -> List[Dict]:
        async with self._pool.acquire() as conn:
            today = date.today()
            rows = await conn.fetch('''
                SELECT DISTINCT u.user_id, u.name, u.tandem_id
                FROM users u
                WHERE u.tandem_id IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1 FROM task_completions tc
                        WHERE tc.user_id = u.user_id
                            AND tc.task_id = ANY($1)
                            AND tc.completed_date = $2
                    )
            ''', task_ids, today)
            return [dict(row) for row in rows]
