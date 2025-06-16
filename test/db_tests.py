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


asyncio.run(main())
