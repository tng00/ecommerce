CREATE SEQUENCE products_id_seq START WITH 1 INCREMENT BY 1;

INSERT INTO "products" (
  "id", "name", "slug", "description", "price", "image_url", 
  "stock", "category_id", "rating", "is_active", "supplier_id"
) VALUES
-- Category: Аксессуары
(nextval('products_id_seq'), 'Accessory Product 1', 'accessory-product-1', 'This is a product from Аксессуары category.', 100, '/static/media/no_photo.png', 20, 50, 0.0, true, 1),
(nextval('products_id_seq'), 'Accessory Product 2', 'accessory-product-2', 'This is a product from Аксессуары category.', 200, '/static/media/no_photo.png', 20, 50, 0.0, true, 1),
(nextval('products_id_seq'), 'Accessory Product 3', 'accessory-product-3', 'This is a product from Аксессуары category.', 300, '/static/media/no_photo.png', 20, 50, 0.0, true, 1),
(nextval('products_id_seq'), 'Accessory Product 4', 'accessory-product-4', 'This is a product from Аксессуары category.', 400, '/static/media/no_photo.png', 20, 50, 0.0, true, 1),
(nextval('products_id_seq'), 'Accessory Product 5', 'accessory-product-5', 'This is a product from Аксессуары category.', 500, '/static/media/no_photo.png', 20, 50, 0.0, true, 1),
(nextval('products_id_seq'), 'Accessory Product 6', 'accessory-product-6', 'This is a product from Аксессуары category.', 600, '/static/media/no_photo.png', 20, 50, 0.0, true, 1),
(nextval('products_id_seq'), 'Accessory Product 7', 'accessory-product-7', 'This is a product from Аксессуары category.', 700, '/static/media/no_photo.png', 20, 50, 0.0, true, 1),
(nextval('products_id_seq'), 'Accessory Product 8', 'accessory-product-8', 'This is a product from Аксессуары category.', 800, '/static/media/no_photo.png', 20, 50, 0.0, true, 1),
(nextval('products_id_seq'), 'Accessory Product 9', 'accessory-product-9', 'This is a product from Аксессуары category.', 900, '/static/media/no_photo.png', 20, 50, 0.0, true, 1),
(nextval('products_id_seq'), 'Accessory Product 10', 'accessory-product-10', 'This is a product from Аксессуары category.', 1000, '/static/media/no_photo.png', 20, 50, 0.0, true, 1),

-- Category: Игровые консоли
(nextval('products_id_seq'), 'Console Product 1', 'console-product-1', 'This is a product from Игровые консоли category.', 100, '/static/media/no_photo.png', 20, 51, 0.0, true, 1),
(nextval('products_id_seq'), 'Console Product 2', 'console-product-2', 'This is a product from Игровые консоли category.', 200, '/static/media/no_photo.png', 20, 51, 0.0, true, 1),
(nextval('products_id_seq'), 'Console Product 3', 'console-product-3', 'This is a product from Игровые консоли category.', 300, '/static/media/no_photo.png', 20, 51, 0.0, true, 1),
(nextval('products_id_seq'), 'Console Product 4', 'console-product-4', 'This is a product from Игровые консоли category.', 400, '/static/media/no_photo.png', 20, 51, 0.0, true, 1),
(nextval('products_id_seq'), 'Console Product 5', 'console-product-5', 'This is a product from Игровые консоли category.', 500, '/static/media/no_photo.png', 20, 51, 0.0, true, 1),
(nextval('products_id_seq'), 'Console Product 6', 'console-product-6', 'This is a product from Игровые консоли category.', 600, '/static/media/no_photo.png', 20, 51, 0.0, true, 1),
(nextval('products_id_seq'), 'Console Product 7', 'console-product-7', 'This is a product from Игровые консоли category.', 700, '/static/media/no_photo.png', 20, 51, 0.0, true, 1),
(nextval('products_id_seq'), 'Console Product 8', 'console-product-8', 'This is a product from Игровые консоли category.', 800, '/static/media/no_photo.png', 20, 51, 0.0, true, 1),
(nextval('products_id_seq'), 'Console Product 9', 'console-product-9', 'This is a product from Игровые консоли category.', 900, '/static/media/no_photo.png', 20, 51, 0.0, true, 1),
(nextval('products_id_seq'), 'Console Product 10', 'console-product-10', 'This is a product from Игровые консоли category.', 1000, '/static/media/no_photo.png', 20, 51, 0.0, true, 1),

-- Category: Игры
(nextval('products_id_seq'), 'Game Product 1', 'game-product-1', 'This is a product from Игры category.', 100, '/static/media/no_photo.png', 20, 52, 0.0, true, 1),
(nextval('products_id_seq'), 'Game Product 2', 'game-product-2', 'This is a product from Игры category.', 200, '/static/media/no_photo.png', 20, 52, 0.0, true, 1),
(nextval('products_id_seq'), 'Game Product 3', 'game-product-3', 'This is a product from Игры category.', 300, '/static/media/no_photo.png', 20, 52, 0.0, true, 1),
(nextval('products_id_seq'), 'Game Product 4', 'game-product-4', 'This is a product from Игры category.', 400, '/static/media/no_photo.png', 20, 52, 0.0, true, 1),
(nextval('products_id_seq'), 'Game Product 5', 'game-product-5', 'This is a product from Игры category.', 500, '/static/media/no_photo.png', 20, 52, 0.0, true, 1),
(nextval('products_id_seq'), 'Game Product 6', 'game-product-6', 'This is a product from Игры category.', 600, '/static/media/no_photo.png', 20, 52, 0.0, true, 1),
(nextval('products_id_seq'), 'Game Product 7', 'game-product-7', 'This is a product from Игры category.', 700, '/static/media/no_photo.png', 20, 52, 0.0, true, 1),
(nextval('products_id_seq'), 'Game Product 8', 'game-product-8', 'This is a product from Игры category.', 800, '/static/media/no_photo.png', 20, 52, 0.0, true, 1),
(nextval('products_id_seq'), 'Game Product 9', 'game-product-9', 'This is a product from Игры category.', 900, '/static/media/no_photo.png', 20, 52, 0.0, true, 1),
(nextval('products_id_seq'), 'Game Product 10', 'game-product-10', 'This is a product from Игры category.', 1000, '/static/media/no_photo.png', 20, 52, 0.0, true, 1);
