DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS users CASCADE;


CREATE TABLE "users" (
  "id" serial PRIMARY KEY,
  "first_name" varchar NOT NULL,
  "last_name" varchar NOT NULL,
  "username" varchar UNIQUE NOT NULL,
  "email" varchar UNIQUE NOT NULL,
  "hashed_password" varchar NOT NULL,
  "is_active" bool NOT NULL DEFAULT true,
  "is_admin" bool NOT NULL DEFAULT false,
  "is_supplier" bool NOT NULL DEFAULT false,
  "is_customer" bool NOT NULL DEFAULT false
);

CREATE TABLE "categories" (
  "id" serial PRIMARY KEY,
  "name" varchar NOT NULL,
  "slug" varchar UNIQUE NOT NULL,
  "is_active" bool NOT NULL DEFAULT true,
  "parent_id" integer DEFAULT NULL
);

CREATE TABLE "products" (
  "id" serial PRIMARY KEY,
  "name" varchar NOT NULL,
  "slug" varchar UNIQUE NOT NULL,
  "description" text,
  "price" integer NOT NULL,
  "image_url" varchar,
  "stock" integer NOT NULL DEFAULT 0,
  "category_id" integer NOT NULL,
  "rating" float NOT NULL DEFAULT 0.0,
  "is_active" bool NOT NULL DEFAULT true,
  "supplier_id" integer NOT NULL
);

CREATE TABLE "orders" (
  "id" serial PRIMARY KEY,
  "user_id" integer NOT NULL,
  "payment_id" integer UNIQUE,
  "order_date" timestamp NOT NULL,
  "address" varchar NOT NULL,
  "status" varchar NOT NULL DEFAULT 'processing',
  "total_amount" integer NOT NULL
);

CREATE TABLE "order_items" (
  "id" serial PRIMARY KEY,
  "order_id" integer NOT NULL,
  "product_id" integer NOT NULL,
  "quantity" integer NOT NULL,
  "price" integer NOT NULL
);

CREATE TABLE "payments" (
  "id" serial PRIMARY KEY,
  "is_card" bool NOT NULL,
  "is_sbp" bool NOT NULL
);

CREATE TABLE "reviews" (
  "id" serial PRIMARY KEY,
  "product_id" integer NOT NULL,
  "user_id" integer NOT NULL,
  "rating" integer NOT NULL,
  "comment" text
);

ALTER TABLE "categories" ADD FOREIGN KEY ("parent_id") REFERENCES "categories" ("id");

ALTER TABLE "products" ADD FOREIGN KEY ("category_id") REFERENCES "categories" ("id");

ALTER TABLE "products" ADD FOREIGN KEY ("supplier_id") REFERENCES "users" ("id");

ALTER TABLE "orders" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "orders" ADD FOREIGN KEY ("payment_id") REFERENCES "payments" ("id");

ALTER TABLE "order_items" ADD FOREIGN KEY ("order_id") REFERENCES "orders" ("id");

ALTER TABLE "order_items" ADD FOREIGN KEY ("product_id") REFERENCES "products" ("id");

ALTER TABLE "reviews" ADD FOREIGN KEY ("product_id") REFERENCES "products" ("id");

ALTER TABLE "reviews" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");