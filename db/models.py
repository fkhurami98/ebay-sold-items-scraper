from sqlalchemy import Column, String, Date, Float, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    price = Column(Float)
    seller_info = Column(String)
    shipping_detail = Column(String)
    listing_type = Column(String)
    item_condition = Column(String)
    sold_date = Column(Date)
