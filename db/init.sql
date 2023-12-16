CREATE TABLE listings (
  id SERIAL PRIMARY KEY,
  title VARCHAR(255),
  price DECIMAL(10, 2),
  seller_info VARCHAR(255),
  shipping_detail VARCHAR(255),
  listing_type VARCHAR(100),
  item_condition VARCHAR(100),
  sold_date DATE
);
