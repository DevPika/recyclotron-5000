from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Customer(Base):
    __tablename__ = 'customer'
    cust_id = Column(Integer, primary_key=True)
    phone_no = Column(String(10), unique=True, nullable=False)

    # keep python decimal vs float in mind
    balance = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)

class Rate(Base):
    __tablename__ = 'rate'
    item_id = Column(Integer, primary_key=True)
    item_name = Column(String(20))

    # keep python decimal vs float in mind
    base_rate = Column(Float, nullable=False)


# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
engine = create_engine('sqlite:///shop.db')
 
# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)
