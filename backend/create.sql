create database persona_project;
show databases;
use persona_project;
CREATE TABLE users (
    id INT(11) NOT NULL AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(200) NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY (username) -- Assuming username should be unique
);
CREATE TABLE persona_flow (
    id INT(11) NOT NULL AUTO_INCREMENT,
    user_id INT(11) NOT NULL,
    character_name VARCHAR(100) NOT NULL,
    mode ENUM('auto', 'custom') NOT NULL,
    tone VARCHAR(50),
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE persona_messages (
    id INT(11) NOT NULL AUTO_INCREMENT,
    persona_id INT(11) NOT NULL,
    sender ENUM('user', 'agent') NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (persona_id) REFERENCES persona_flow(id) ON DELETE CASCADE
);
show tables;