CREATE OR REPLACE FUNCTION get_all_categories()
RETURNS TABLE(id INT, is_active BOOLEAN, parent_id INT, name VARCHAR, slug VARCHAR) AS
$$
BEGIN
    RETURN QUERY
    SELECT 
        c.id, 
        c.is_active, 
        c.parent_id, 
        c.name, 
        c.slug
    FROM 
        categories c
    ORDER BY 
        c.id;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION create_category_function(
    category_name VARCHAR, 
    category_slug VARCHAR,
    category_parent_id INT DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    DELETE FROM categories WHERE slug = category_slug AND is_active = FALSE;
    INSERT INTO categories (name, parent_id, slug, is_active)  
    VALUES (category_name, category_parent_id, category_slug, TRUE); 
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION update_category_function(
    category_id INT,
    category_name VARCHAR,
    category_parent_id INT,
    category_slug VARCHAR
)
RETURNS VOID AS
$$
BEGIN
    UPDATE categories
    SET name = category_name,
        slug = category_slug,
        parent_id = category_parent_id
    WHERE id = category_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Category with id % not found', category_id;
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION delete_category_function(
    category_id INT
)
RETURNS VOID AS
$$
DECLARE
    category_ids_to_deactivate INT[];
BEGIN
    WITH RECURSIVE category_tree AS (
        SELECT id
        FROM categories
        WHERE id = category_id
        UNION ALL
        SELECT c.id
        FROM categories c
        INNER JOIN category_tree ct ON c.parent_id = ct.id
    )
    SELECT array_agg(id) INTO category_ids_to_deactivate FROM category_tree;

    UPDATE categories
    SET is_active = FALSE
    WHERE id = ANY(category_ids_to_deactivate);
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION create_user_function(
    p_first_name VARCHAR,
    p_last_name VARCHAR,
    p_username VARCHAR,
    p_email VARCHAR,
    p_password VARCHAR,
    p_is_active BOOLEAN DEFAULT TRUE,
    p_is_admin BOOLEAN DEFAULT FALSE,
    p_is_supplier BOOLEAN DEFAULT FALSE,
    p_is_customer BOOLEAN DEFAULT TRUE
)
RETURNS INTEGER AS
$$
DECLARE
    new_user_id INTEGER;
BEGIN
    INSERT INTO users (
        first_name, 
        last_name, 
        username, 
        email, 
        hashed_password, 
        is_active, 
        is_admin, 
        is_supplier, 
        is_customer
    ) VALUES (
        p_first_name, 
        p_last_name, 
        p_username, 
        p_email, 
        p_password, 
        p_is_active, 
        p_is_admin, 
        p_is_supplier, 
        p_is_customer
    ) RETURNING id INTO new_user_id;

    RETURN new_user_id;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_active_products()
RETURNS TABLE(
    id INT,
    category_id INT,
    rating DOUBLE PRECISION,
    is_active BOOLEAN,
    supplier_id INT,
    price INT,
    stock INT,
    name VARCHAR,
    slug VARCHAR,
    description TEXT,
    image_url VARCHAR,
    category_name VARCHAR 
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.category_id,
        p.rating,
        p.is_active,
        p.supplier_id,
        p.price,
        p.stock,
        p.name,
        p.slug,
        p.description,
        p.image_url,
        c.name AS category_name
    FROM products p
    JOIN categories c ON p.category_id = c.id 
    WHERE p.is_active = TRUE;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION create_product_function(
    product_name VARCHAR,
    product_description TEXT,
    product_price INT,
    product_image_extension VARCHAR,
    product_stock INT,
    product_category_id INT,
    product_slug VARCHAR,
    product_supplier_id INT,
    product_rating DOUBLE PRECISION DEFAULT 0.0
)
RETURNS INT AS $$
DECLARE
    new_product_id INT;
    new_image_url VARCHAR;
BEGIN
    INSERT INTO products (
        name, 
        description, 
        price, 
        image_url,
        stock, 
        category_id, 
        rating, 
        slug, 
        supplier_id,
        is_active
    ) 
    VALUES (
        product_name, 
        product_description, 
        product_price, 
        '',
        product_stock, 
        product_category_id, 
        product_rating, 
        product_slug, 
        product_supplier_id,
        TRUE
    )
    RETURNING id INTO new_product_id;

    new_image_url := CONCAT(new_product_id, '.', product_image_extension);

    UPDATE products
    SET image_url = new_image_url
    WHERE id = new_product_id;

    RETURN new_product_id;
END;
$$ LANGUAGE plpgsql;




CREATE OR REPLACE FUNCTION get_products_by_category(category_slug_input VARCHAR)
RETURNS TABLE(
    product_id INT,
    product_name VARCHAR,
    product_description text,
    product_price INT,
    product_image_url VARCHAR,
    product_stock INT,
    product_rating DOUBLE PRECISION,
    category_id INT,
    product_slug VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE category_tree AS (
        SELECT id
        FROM categories
        WHERE slug = category_slug_input

        UNION ALL

        SELECT c.id
        FROM categories c
        INNER JOIN category_tree ct ON c.parent_id = ct.id
    )
    SELECT 
        p.id AS product_id,
        p.name AS product_name,
        p.description AS product_description,
        p.price AS product_price,
        p.image_url AS product_image_url,
        p.stock AS product_stock,
        p.rating AS product_rating,
        p.category_id AS category_id,
        p.slug AS product_slug
    FROM products p
    WHERE p.category_id IN (SELECT id FROM category_tree)
      AND p.is_active = TRUE;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_product_detail_by_slug(product_slug_input VARCHAR)
RETURNS TABLE(
    product_id INT,
    product_name VARCHAR,
    product_description text,
    product_price INT,
    product_image_url VARCHAR,
    product_stock INT,
    product_rating DOUBLE PRECISION,
    category_id INT,
    product_slug VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id AS product_id,
        p.name AS product_name,
        p.description AS product_description,
        p.price AS product_price,
        p.image_url AS product_image_url,
        p.stock AS product_stock,
        p.rating AS product_rating,
        p.category_id AS category_id,
        p.slug AS product_slug
    FROM products p
    WHERE p.slug = product_slug_input
      AND p.is_active = TRUE;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION update_product_function(
    product_slug_input VARCHAR,
    product_name VARCHAR,
    product_description text,
    product_price INT,
    product_image_url VARCHAR,
    product_stock INT,
    product_category_id INT,
    product_slug VARCHAR
)
RETURNS VOID AS
$$
BEGIN
    IF EXISTS (SELECT 1 FROM products WHERE slug = product_slug_input AND is_active = TRUE) THEN
        UPDATE products
        SET
            name = product_name,
            description = product_description,
            price = product_price,
            image_url = product_image_url,
            stock = product_stock,
            category_id = product_category_id,
            slug = product_slug
        WHERE slug = product_slug_input;
    ELSE
        RAISE EXCEPTION 'Product not found or is not active';
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION insert_payment(
    is_card BOOLEAN,
    is_sbp BOOLEAN
) RETURNS INTEGER AS $$
DECLARE
    new_payment_id INTEGER;
BEGIN
    INSERT INTO payments (is_card, is_sbp)
    VALUES (is_card, is_sbp)
    RETURNING id INTO new_payment_id;

    RETURN new_payment_id;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION insert_order(
    user_id INTEGER,
    payment_id INTEGER,
    order_date TIMESTAMP,
    address VARCHAR,
    total INTEGER,
    status VARCHAR DEFAULT 'В обработке'
) RETURNS INTEGER AS $$
DECLARE
    new_order_id INTEGER;
BEGIN
    -- Вставка нового заказа
    INSERT INTO orders (user_id, payment_id, order_date, address, total, status)
    VALUES (user_id, payment_id, order_date, address, total, status)
    RETURNING id INTO new_order_id;

    RETURN new_order_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION create_order(
    is_card BOOLEAN,
    is_sbp BOOLEAN,
    user_id INTEGER,
    order_date TIMESTAMP,
    address VARCHAR,
    total INTEGER,
    status VARCHAR DEFAULT 'В обработке'
) RETURNS INTEGER AS $$
DECLARE
    new_payment_id INTEGER;
    new_order_id INTEGER;
BEGIN
    new_payment_id := insert_payment(is_card, is_sbp);

    new_order_id := insert_order(user_id, new_payment_id, order_date, address, total, status);

    RETURN new_order_id; 
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_all_orders()
RETURNS TABLE (
    id INTEGER,
    user_id INTEGER,
    payment_id INTEGER,
    order_date TIMESTAMP,
    address VARCHAR,
    total INTEGER,
    status VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.id,
        o.user_id,
        o.payment_id,
        o.order_date,
        o.address,
        o.total,
        o.status
    FROM 
        orders o;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_active_reviews()
RETURNS TABLE(
    id INT,
    product_id INT,
    user_id INT,
    rating INT,
    comment TEXT,
    product_name VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.product_id,
        r.user_id,
        r.rating,
        r.comment,
        p.name
    FROM reviews r
    JOIN products p ON r.product_id = p.id
    WHERE p.is_active = TRUE;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION create_review_function(
    review_product_id INT,
    review_user_id INT,
    review_rating INT,
    review_comment TEXT
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO reviews (
        product_id, 
        user_id, 
        rating, 
        comment
    ) 
    VALUES (
        review_product_id, 
        review_user_id, 
        review_rating, 
        review_comment
    );
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION reduce_stock()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE products
    SET stock = stock - NEW.quantity
    WHERE id = NEW.product_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_reduce_stock
AFTER INSERT ON order_items
FOR EACH ROW
EXECUTE FUNCTION reduce_stock();



CREATE OR REPLACE FUNCTION update_product_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE products
    SET rating = (
        SELECT AVG(rating)
        FROM reviews
        WHERE product_id = NEW.product_id
    )
    WHERE id = NEW.product_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_product_rating
AFTER INSERT ON reviews
FOR EACH ROW
EXECUTE FUNCTION update_product_rating();
