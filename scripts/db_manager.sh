#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Function to create a new database and user
create_database() {
    local dbname=$1
    local username=$2
    local password=$3
    
    # Create database
    sudo -u postgres psql -c "CREATE DATABASE ${dbname};"
    
    # Create user
    sudo -u postgres psql -c "CREATE USER ${username} WITH PASSWORD '${password}';"
    
    # Grant privileges
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${dbname} TO ${username};"
    
    echo -e "${GREEN}Database and user created: ${dbname}${NC}"
}

# Function to remove a database and user
remove_database() {
    local dbname=$1
    local username=$2
    
    # Drop database
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${dbname};"
    
    # Drop user
    sudo -u postgres psql -c "DROP USER IF EXISTS ${username};"
    
    echo -e "${GREEN}Database and user removed: ${dbname}${NC}"
}

# Function to change database user password
change_password() {
    local username=$1
    local new_password=$2
    
    # Change password
    sudo -u postgres psql -c "ALTER USER ${username} WITH PASSWORD '${new_password}';"
    
    echo -e "${GREEN}Password changed for user: ${username}${NC}"
}

# Function to backup a database
backup_database() {
    local dbname=$1
    local backup_path=$2
    
    # Create backup
    sudo -u postgres pg_dump ${dbname} > "${backup_path}"
    
    echo -e "${GREEN}Database backed up to: ${backup_path}${NC}"
}

# Function to restore a database from backup
restore_database() {
    local dbname=$1
    local backup_path=$2
    
    # Restore from backup
    sudo -u postgres psql ${dbname} < "${backup_path}"
    
    echo -e "${GREEN}Database restored from: ${backup_path}${NC}"
}

# Main script
case "$1" in
    create)
        if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
            echo "Usage: $0 create <dbname> <username> <password>"
            exit 1
        fi
        create_database "$2" "$3" "$4"
        ;;
    remove)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 remove <dbname> <username>"
            exit 1
        fi
        remove_database "$2" "$3"
        ;;
    password)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 password <username> <new_password>"
            exit 1
        fi
        change_password "$2" "$3"
        ;;
    backup)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 backup <dbname> <backup_path>"
            exit 1
        fi
        backup_database "$2" "$3"
        ;;
    restore)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 restore <dbname> <backup_path>"
            exit 1
        fi
        restore_database "$2" "$3"
        ;;
    *)
        echo "Usage: $0 {create|remove|password|backup|restore} [dbname/username] [username/password/backup_path]"
        exit 1
        ;;
esac

exit 0 