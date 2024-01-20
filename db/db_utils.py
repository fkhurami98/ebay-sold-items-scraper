from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Listing
from app.settings import DATABASE_URI



engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

def insert_data(data):
    session = Session()
    for item in data:
        exists = session.query(Listing).filter_by(title=item["title"], sold_date=item["sold_date"]).first() is not None
        if not exists:
            listing = Listing(
                title=item["title"],
                price=item["price"],
                seller_info=item["seller_info"],
                shipping_detail=item["shipping_detail"],
                listing_type=item["listing_type"],
                item_condition=item["item_condition"],
                sold_date=item["sold_date"]
            )
            session.add(listing)
    session.commit()
    session.close()

# Uncomment the next line if you need to create the table
# Base.metadata.create_all(engine)
