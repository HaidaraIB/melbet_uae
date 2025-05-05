import os
import sys
from dotenv import load_dotenv
import asyncio
import sqlalchemy.exc

# Add the project root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models


async def main():
    load_dotenv()
    models.init_db()
    timer = models.SessionTimer(uid=1, gid=1, end_time=4)
    with models.session_scope() as s:
        s.query(models.SessionTimer).filter(models.SessionTimer.uid == 1, models.SessionTimer.gid == 1).delete()
        s.commit()




asyncio.run(main())
