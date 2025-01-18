from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from datetime import datetime
from services.database import Base

class Roles(Base):
    __tablename__ = "roles"
    role_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    role_name = Column(String, nullable=False, unique=True)
    color_code = Column(String)

    permissions = relationship("RolePermission", back_populates="role")

class Pages(Base):
    __tablename__ = "pages"
    page_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    page_name = Column(String, nullable=False, unique=True)
    page_path = Column(String, nullable=False)

    permissions = relationship("RolePermission", back_populates="page")

class RolePermission(Base):
    __tablename__ = "role_permission"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    role_id = Column(Integer, ForeignKey('roles.role_id'))
    page_id = Column(Integer, ForeignKey('pages.page_id'))

    role = relationship("Roles", back_populates="permissions")
    page = relationship("Pages", back_populates="permissions")

class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone_number = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    city = Column(String)
    country = Column(String)
    role_id = Column(Integer, ForeignKey('roles.role_id'))
    created_date = Column(DateTime, default=func.now())

    annotations = relationship("Annotation", back_populates="user")

class CurveCoinPrice(Base):
    __tablename__ = "crv_data"
    id = Column(Integer, primary_key=True, index=True)
    open_time = Column(DateTime)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    close_time = Column(DateTime)
    quote_asset_volume = Column(Float)
    number_of_trades = Column(Float)
    taker_buy_base_asset_volume = Column(Float)
    ignore = Column(Float)

class KadenaPrice(Base):
    __tablename__ = "kda_data"
    id = Column(Integer, primary_key=True, index=True)
    open_time = Column(DateTime)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    close_time = Column(DateTime)
    quote_asset_volume = Column(Float)
    number_of_trades = Column(Float)
    taker_buy_base_asset_volume = Column(Float)
    ignore = Column(Float)

class CetusPrice(Base):
    __tablename__ = "cetus_data"
    id = Column(Integer, primary_key=True, index=True)
    open_time = Column(DateTime)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    close_time = Column(DateTime)
    quote_asset_volume = Column(Float)
    number_of_trades = Column(Float)
    taker_buy_base_asset_volume = Column(Float)
    ignore = Column(Float)

class BitcoinPrice(Base):
    __tablename__ = "btc_data"
    id = Column(Integer, primary_key=True, index=True)
    open_time = Column(DateTime)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    close_time = Column(DateTime)
    quote_asset_volume = Column(Float)
    number_of_trades = Column(Float)
    taker_buy_base_asset_volume = Column(Float)
    ignore = Column(Float)

class EthereumPrice(Base):
    __tablename__ = "eth_data"
    id = Column(Integer, primary_key=True, index=True)
    open_time = Column(DateTime)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    close_time = Column(DateTime)
    quote_asset_volume = Column(Float)
    number_of_trades = Column(Float)
    taker_buy_base_asset_volume = Column(Float)
    ignore = Column(Float)

class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stock_symbol = Column(String, index=True, nullable=False)
    x_coord = Column(Float, nullable=False)
    y_coord = Column(Float, nullable=False)
    text = Column(String, nullable=False)
    title = Column(String, nullable=True)
    annotation_type = Column(String, nullable=True)  # Örn: 'note', 'warning', 'info'
    status = Column(String, default="active")  # Örn: 'active', 'inactive'
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("Users", back_populates="annotations")

# class Annotation(Base):
#     __tablename__ = "annotations"

#     id = Column(Integer, primary_key=True, index=True, autoincrement=True)
#     stock_symbol = Column(String, index=True)
#     x_coord = Column(Float)
#     y_coord = Column(Float)
#     text = Column(String)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     created_at = Column(DateTime, default=func.now())
#     updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

#     user = relationship("Users", back_populates="annotations")