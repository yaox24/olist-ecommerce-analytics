-- ============================================================
-- OLIST E-COMMERCE ANALYTICS PROJECT
-- Phase 6: SQL Analytics
-- Author: Ziyao Xing
-- Purpose: Answer business questions using PostgreSQL
-- ============================================================
-- ============================================================
-- SECTION 1: REVENUE OVERVIEW
-- ============================================================

-- Query 1: Total delivered revenue
-- Business question: How much revenue did delivered orders generate?

SELECT
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.price + oi.freight_value)::numeric, 2) AS total_revenue,
    ROUND(AVG(oi.price + oi.freight_value)::numeric, 2) AS avg_item_value
FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered';



-- Query 2: Monthly revenue trend
-- Business question: How did revenue change over time?

SELECT
    DATE_TRUNC('month', o.order_purchase_timestamp) AS month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.price + oi.freight_value)::numeric, 2) AS total_revenue
FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY month
ORDER BY month;


-- Query 3: Revenue by customer state
-- Business question: Which states generate the most revenue?

SELECT
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.price + oi.freight_value)::numeric, 2) AS total_revenue,
    ROUND(AVG(oi.price + oi.freight_value)::numeric, 2) AS avg_item_value
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN order_items oi
    ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY total_revenue DESC;



-- ============================================================
-- SECTION 2: PRODUCT ANALYSIS
-- ============================================================

-- Query 4: Top product categories by revenue
-- Business question: Which product categories drive the most revenue?

SELECT
    COALESCE(t.product_category_name_english, p.product_category_name) AS category,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    ROUND(SUM(oi.price)::numeric, 2) AS product_revenue,
    ROUND(AVG(oi.price)::numeric, 2) AS avg_item_price
FROM order_items oi
JOIN products p
    ON oi.product_id = p.product_id
LEFT JOIN product_category_translation t
    ON p.product_category_name = t.product_category_name
JOIN orders o
    ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY category
ORDER BY product_revenue DESC
LIMIT 20;



-- ============================================================
-- SECTION 3: CUSTOMER SATISFACTION
-- ============================================================

-- Query 5: Review score distribution
-- Business question: How satisfied are customers overall?

SELECT
    review_score,
    COUNT(*) AS review_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_reviews
FROM order_reviews
GROUP BY review_score
ORDER BY review_score;




-- Query 6: Average review score by delivery status
-- Business question: Do late deliveries reduce customer satisfaction?

SELECT
    CASE
        WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
            THEN 'Late'
        ELSE 'On Time'
    END AS delivery_status,
    COUNT(*) AS review_count,
    ROUND(AVG(r.review_score)::numeric, 2) AS avg_review_score
FROM orders o
JOIN order_reviews r
    ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
    AND o.order_estimated_delivery_date IS NOT NULL
GROUP BY delivery_status
ORDER BY avg_review_score DESC;



-- ============================================================
-- SECTION 4: CUSTOMER ANALYSIS
-- ============================================================

-- Query 7: Repeat purchase rate
-- Business question: What percentage of customers purchased more than once?

WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS order_count
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)

SELECT
    COUNT(*) AS total_customers,
    SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    ROUND(
        SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS repeat_purchase_rate_pct
FROM customer_orders;



-- Query 8: Top 10 customers by lifetime revenue
-- Business question: Who are the highest-value customers?

SELECT
    c.customer_unique_id,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.price + oi.freight_value)::numeric, 2) AS lifetime_revenue
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN order_items oi
    ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_unique_id
ORDER BY lifetime_revenue DESC
LIMIT 10;



-- ============================================================
-- SECTION 5: SELLER ANALYSIS
-- ============================================================

-- Query 9: Top sellers by revenue
-- Business question: Which sellers generate the most revenue?

SELECT
    s.seller_id,
    s.seller_state,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    ROUND(SUM(oi.price)::numeric, 2) AS seller_revenue
FROM sellers s
JOIN order_items oi
    ON s.seller_id = oi.seller_id
JOIN orders o
    ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY s.seller_id, s.seller_state
ORDER BY seller_revenue DESC
LIMIT 20;



-- ============================================================
-- SECTION 6: ADVANCED SQL
-- ============================================================

-- Query 10: Month-over-month revenue growth
-- Business question: How quickly is revenue growing each month?

WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', o.order_purchase_timestamp) AS month,
        SUM(oi.price + oi.freight_value) AS revenue
    FROM orders o
    JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY month
)

SELECT
    month,
    ROUND(revenue::numeric, 2) AS revenue,
    ROUND(LAG(revenue) OVER (ORDER BY month)::numeric, 2) AS previous_month_revenue,
    ROUND(
        ((revenue - LAG(revenue) OVER (ORDER BY month))
        / NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100)::numeric,
        2
    ) AS mom_growth_pct
FROM monthly_revenue
ORDER BY month;



