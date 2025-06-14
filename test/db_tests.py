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
    with models.session_scope() as s:
        s.add(models.Receipt(id=1, payment_method_id=1))
        s.commit()
        s.add(
            models.Transaction(
                user_id=755501092,
                payment_method_id=1,
                type="deposit",
                amount=1,
                currency="aed",
                receipt_id=1,
                player_account=1,
            )
        )
        s.commit()
        r = s.get(models.Receipt, 1)
        print(r.payment_method)


asyncio.run(main())
