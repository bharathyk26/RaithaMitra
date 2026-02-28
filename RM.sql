/* =========================================================
   FINAL FULL DATABASE SCHEMA – RUN ONCE
   ========================================================= */

DROP DATABASE IF EXISTS krishi_mitra;
CREATE DATABASE krishi_mitra
CHARACTER SET utf8mb4
COLLATE utf8mb4_general_ci;

USE krishi_mitra;

-- =========================================================
-- USERS TABLE
-- =========================================================
CREATE TABLE users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    mobile VARCHAR(15),
    aadhar VARCHAR(12),
    dob DATE,
    location VARCHAR(255),
    pincode VARCHAR(6),
    land_size DECIMAL(10,2),
    profile_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =========================================================
-- ADMIN USERS
-- =========================================================
CREATE TABLE admin_users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(255),
    role VARCHAR(50) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =========================================================
-- CROP LIMITS
-- =========================================================
CREATE TABLE crop_limits (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    crop_name VARCHAR(100) UNIQUE NOT NULL,
    daily_limit_tonnes DECIMAL(10,2) NOT NULL,
    current_applications_tonnes DECIMAL(10,2) DEFAULT 0,
    season VARCHAR(50),
    base_price_per_kg DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'OPEN',
    last_reset_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =========================================================
-- DISEASE REPORTS
-- =========================================================
CREATE TABLE disease_reports (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    report_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INT UNSIGNED NOT NULL,
    username VARCHAR(100) NOT NULL,
    farmer_name VARCHAR(200) NOT NULL,
    mobile VARCHAR(15),
    crop_name VARCHAR(100) NOT NULL,
    location VARCHAR(255),
    disease_description TEXT,
    photo_path VARCHAR(500),
    status VARCHAR(50) DEFAULT 'Pending',
    admin_response TEXT,
    recommended_medicine TEXT,
    responded_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP NULL,
    CONSTRAINT fk_disease_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- =========================================================
-- SOIL RECOMMENDATIONS
-- =========================================================
CREATE TABLE crop_soil_recommendations (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    soil_type VARCHAR(100) NOT NULL,
    recommended_crops TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =========================================================
-- CROP APPLICATIONS (ALL COLUMNS INCLUDED – NO ALTER NEEDED)
-- =========================================================
CREATE TABLE crop_applications (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    application_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INT UNSIGNED NOT NULL,
    username VARCHAR(100) NOT NULL,
    farmer_name VARCHAR(200) NOT NULL,
    mobile VARCHAR(15) NOT NULL,
    location VARCHAR(255) NOT NULL,
    crop_name VARCHAR(100) NOT NULL,
    crop_variety VARCHAR(100),
    land_area DECIMAL(10,2) NOT NULL,
    expected_yield DECIMAL(10,2),
    estimated_quantity_tonnes DECIMAL(10,2) DEFAULT 0,
    planting_date DATE,
    expected_harvest_date DATE,
    estimated_price_per_kg DECIMAL(10,2),
    price_at_application DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'Planned',
    limit_status VARCHAR(50) DEFAULT 'Within Limit',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_crop_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- =========================================================
-- INSURANCE APPLICATIONS
-- =========================================================
CREATE TABLE insurance_applications (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    application_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INT UNSIGNED NOT NULL,
    username VARCHAR(100) NOT NULL,
    farmer_name VARCHAR(200) NOT NULL,
    aadhar VARCHAR(12) NOT NULL,
    mobile VARCHAR(15) NOT NULL,
    dob DATE NOT NULL,
    location VARCHAR(255) NOT NULL,
    pincode VARCHAR(6) NOT NULL,
    plan_id VARCHAR(50) NOT NULL,
    plan_name VARCHAR(200) NOT NULL,
    crop_type VARCHAR(100) NOT NULL,
    land_size DECIMAL(10,2) NOT NULL,
    premium DECIMAL(10,2) NOT NULL,
    coverage VARCHAR(50) NOT NULL,
    applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Pending Approval',
    validity_start DATE,
    validity_end DATE,
    CONSTRAINT fk_insurance_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- =========================================================
-- MARKET PRICES
-- =========================================================
CREATE TABLE crop_market_prices (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    crop_name VARCHAR(100) NOT NULL,
    price_per_kg DECIMAL(10,2) NOT NULL,
    location VARCHAR(255),
    market_date DATE NOT NULL,
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_crop_date (crop_name, market_date)
) ENGINE=InnoDB;

-- =========================================================
-- PRODUCTS
-- =========================================================
CREATE TABLE products (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    quantity VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    seller VARCHAR(200) NOT NULL,
    location VARCHAR(255) NOT NULL,
    contact VARCHAR(15) NOT NULL,
    icon VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =========================================================
-- SAMPLE USERS
-- =========================================================
INSERT INTO users (username, password_hash, full_name, mobile, location, land_size, profile_completed)
VALUES ('farmer', 'hash123', 'Ramesh Kumar', '9876543210', 'Anekal, Bengaluru', 5.5, TRUE);

INSERT INTO admin_users (username, password_hash, full_name, email)
VALUES ('admin', 'scrypt:32768:8:1$whl1JkUPvVy1kMPe$511a4ceab2a18467aa1bd20e878c382052aaeff8cec365a7f43deb8fb58777dccdaa139cd497ba13cd2f7e85b312bc0d85f870f84c6febb343447a79f7281cd2', 'System Admin', 'admin@krishimitra.gov.in');



-- Insert default crop limits
INSERT INTO crop_limits (crop_name, daily_limit_tonnes, base_price_per_kg, season, status) VALUES
('Tomato', 3000.00, 45.00, 'All Season', 'OPEN'),
('Potato', 2500.00, 22.00, 'Rabi', 'OPEN'),
('Onion', 2000.00, 28.00, 'Rabi', 'OPEN'),
('Cabbage', 1500.00, 18.00, 'Rabi', 'OPEN'),
('Cauliflower', 1200.00, 25.00, 'Rabi', 'OPEN'),
('Carrot', 800.00, 30.00, 'Rabi', 'OPEN'),
('Beans', 1000.00, 40.00, 'Kharif', 'OPEN'),
('Brinjal', 1500.00, 35.00, 'All Season', 'OPEN'),
('Ragi', 5000.00, 35.00, 'Kharif', 'OPEN'),
('Paddy', 8000.00, 28.00, 'Kharif', 'OPEN'),
('Maize', 6000.00, 22.00, 'Kharif', 'OPEN'),
('Wheat', 7000.00, 25.00, 'Rabi', 'OPEN'),
('Groundnut', 3000.00, 65.00, 'Kharif', 'OPEN'),
('Soybean', 2500.00, 50.00, 'Kharif', 'OPEN'),
('Cotton', 4000.00, 80.00, 'Kharif', 'OPEN'),
('Sugarcane', 10000.00, 35.00, 'All Season', 'OPEN'),
('Banana', 2000.00, 35.00, 'All Season', 'OPEN'),
('Mango', 1500.00, 60.00, 'Summer', 'OPEN'),
('Coconut', 3000.00, 25.00, 'All Season', 'OPEN')
ON DUPLICATE KEY UPDATE crop_name=crop_name;

-- Insert soil-based crop recommendations
INSERT INTO crop_soil_recommendations (soil_type, recommended_crops) VALUES
('Red Sandy Loam', 'Ragi, Groundnut, Maize, Sunflower, Horsegram'),
('Red Loamy Soil', 'Ragi, Groundnut, Maize, Vegetables, Pulses'),
('Black Cotton Soil', 'Cotton, Jowar, Soybean, Wheat, Bengal Gram'),
('Clay Loam', 'Paddy, Sugarcane, Vegetables'),
('Laterite Soil', 'Coffee, Cashew, Arecanut, Pepper'),
('Red to Laterite Soil', 'Ragi, Coffee, Pepper, Arecanut')
ON DUPLICATE KEY UPDATE soil_type=soil_type;


-- Insert Sample Products
INSERT INTO products (name, category, quantity, price, seller, location, contact, icon) VALUES
('Fresh Tomatoes', 'Vegetables', '50 kg', 30, 'Ramesh Kumar', 'Anekal, Bengaluru', '9876543210', '🍅'),
('Organic Ragi', 'Grains', '2 Quintals', 3500, 'Lakshmi Devi', 'Mandya', '9876543211', '🌾'),
('Red Onions', 'Vegetables', '100 kg', 25, 'Prakash Gowda', 'Mysuru', '9876543212', '🧅'),
('Green Chillies', 'Vegetables', '30 kg', 40, 'Suma M', 'Hassan', '9876543213', '🌶️'),
('Banana', 'Fruits', '200 kg', 35, 'Nagesh Reddy', 'T. Narsipur, Mysuru', '9876543214', '🍌'),
('Toor Dal', 'Pulses', '5 Quintals', 8000, 'Basavaraj Patil', 'Belagavi', '9876543215', '🫘'),
('Coconuts', 'Fruits', '500 pieces', 25, 'Shanta Bai', 'Tumakuru', '9876543216', '🥥'),
('Maize', 'Grains', '3 Quintals', 2000, 'Manjunath H', 'Mandya', '9876543217', '🌽'),
('Turmeric', 'Spices', '50 kg', 120, 'Geetha Rani', 'Nanjangud, Mysuru', '9876543218', '🟡'),
('Potatoes', 'Vegetables', '100 kg', 20, 'Krishna Murthy', 'Hassan', '9876543219', '🥔')
ON DUPLICATE KEY UPDATE name=name;

-- Insert Sample Crop Market Prices
INSERT INTO crop_market_prices (crop_name, price_per_kg, location, market_date, source) VALUES
('Tomato', 45.00, 'Bengaluru', CURDATE(), 'APMC Market'),
('Tomato', 48.00, 'Mysuru', CURDATE(), 'APMC Market'),
('Onion', 28.00, 'Bengaluru', CURDATE(), 'APMC Market'),
('Potato', 22.00, 'Bengaluru', CURDATE(), 'APMC Market'),
('Cabbage', 18.00, 'Bengaluru', CURDATE(), 'APMC Market'),
('Cauliflower', 25.00, 'Bengaluru', CURDATE(), 'APMC Market'),
('Ragi', 35.00, 'Mandya', CURDATE(), 'APMC Market'),
('Paddy', 28.00, 'Mandya', CURDATE(), 'APMC Market'),
('Maize', 22.00, 'Hassan', CURDATE(), 'APMC Market'),
('Groundnut', 65.00, 'Belagavi', CURDATE(), 'APMC Market')
ON DUPLICATE KEY UPDATE price_per_kg=price_per_kg;