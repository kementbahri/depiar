-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create domains table
CREATE TABLE domains (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    ssl_enabled BOOLEAN DEFAULT false,
    ssl_expiry TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create email_accounts table
CREATE TABLE email_accounts (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    domain_id INTEGER REFERENCES domains(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    password VARCHAR(255) NOT NULL,
    quota INTEGER DEFAULT 1000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(username, domain_id)
);

-- Create databases table
CREATE TABLE databases (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_domains_name ON domains(name);
CREATE INDEX idx_domains_user_id ON domains(user_id);
CREATE INDEX idx_email_accounts_domain_id ON email_accounts(domain_id);
CREATE INDEX idx_email_accounts_user_id ON email_accounts(user_id);
CREATE INDEX idx_databases_user_id ON databases(user_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_domains_updated_at
    BEFORE UPDATE ON domains
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_accounts_updated_at
    BEFORE UPDATE ON email_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_databases_updated_at
    BEFORE UPDATE ON databases
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add indexes for better performance
CREATE INDEX idx_domains_customer_id ON domains(customer_id);
CREATE INDEX idx_domains_status ON domains(status);
CREATE INDEX idx_email_accounts_domain_id ON email_accounts(domain_id);
CREATE INDEX idx_email_accounts_user_id ON email_accounts(user_id);
CREATE INDEX idx_databases_user_id ON databases(user_id);
CREATE INDEX idx_ssl_certificates_domain_id ON ssl_certificates(domain_id);
CREATE INDEX idx_dns_records_domain_id ON dns_records(domain_id);
CREATE INDEX idx_ftp_accounts_domain_id ON ftp_accounts(domain_id);
CREATE INDEX idx_scheduled_tasks_domain_id ON scheduled_tasks(domain_id);
CREATE INDEX idx_backups_domain_id ON backups(domain_id);
CREATE INDEX idx_domain_logs_domain_id ON domain_logs(domain_id);
CREATE INDEX idx_domain_logs_created_at ON domain_logs(created_at);
CREATE INDEX idx_customers_service_plan_id ON customers(service_plan_id);
CREATE INDEX idx_customers_reseller_plan_id ON customers(reseller_plan_id);
CREATE INDEX idx_customers_status ON customers(status);
CREATE INDEX idx_service_plans_created_by_id ON service_plans(created_by_id);
CREATE INDEX idx_service_plans_is_active ON service_plans(is_active);
CREATE INDEX idx_service_plans_is_public ON service_plans(is_public);
CREATE INDEX idx_reseller_plans_is_active ON reseller_plans(is_active);

-- Create trigger function for customer statistics
CREATE OR REPLACE FUNCTION update_customer_statistics()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF TG_TABLE_NAME = 'domains' THEN
            UPDATE customers
            SET total_domains = total_domains + 1
            WHERE id = NEW.customer_id;
        ELSIF TG_TABLE_NAME = 'email_accounts' THEN
            UPDATE customers
            SET total_email_accounts = total_email_accounts + 1
            WHERE id = NEW.customer_id;
        ELSIF TG_TABLE_NAME = 'databases' THEN
            UPDATE customers
            SET total_databases = total_databases + 1
            WHERE id = NEW.customer_id;
        END IF;
    ELSIF TG_OP = 'DELETE' THEN
        IF TG_TABLE_NAME = 'domains' THEN
            UPDATE customers
            SET total_domains = total_domains - 1
            WHERE id = OLD.customer_id;
        ELSIF TG_TABLE_NAME = 'email_accounts' THEN
            UPDATE customers
            SET total_email_accounts = total_email_accounts - 1
            WHERE id = OLD.customer_id;
        ELSIF TG_TABLE_NAME = 'databases' THEN
            UPDATE customers
            SET total_databases = total_databases - 1
            WHERE id = OLD.customer_id;
        END IF;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Create triggers for customer statistics
CREATE TRIGGER update_customer_domain_stats
    AFTER INSERT OR DELETE ON domains
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_statistics();

CREATE TRIGGER update_customer_email_stats
    AFTER INSERT OR DELETE ON email_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_statistics();

CREATE TRIGGER update_customer_database_stats
    AFTER INSERT OR DELETE ON databases
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_statistics(); 