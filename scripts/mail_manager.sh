#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Function to create a new email account
create_email_account() {
    local username=$1
    local domain=$2
    local password=$3
    local quota=$4

    # Create user directory
    local maildir="/var/mail/${domain}/${username}"
    mkdir -p "${maildir}"
    
    # Create user
    useradd -m -d "${maildir}" -s /sbin/nologin "${username}@${domain}"
    
    # Set password
    echo "${username}@${domain}:${password}" | chpasswd
    
    # Set quota
    if [ ! -z "$quota" ]; then
        setquota -u "${username}@${domain}" 0 ${quota} 0 0 /var/mail
    fi
    
    # Set permissions
    chown -R "${username}@${domain}:${username}@${domain}" "${maildir}"
    chmod -R 700 "${maildir}"
    
    echo -e "${GREEN}Email account created: ${username}@${domain}${NC}"
}

# Function to remove an email account
remove_email_account() {
    local username=$1
    local domain=$2
    
    # Remove user
    userdel -r "${username}@${domain}"
    
    # Remove mail directory
    rm -rf "/var/mail/${domain}/${username}"
    
    echo -e "${GREEN}Email account removed: ${username}@${domain}${NC}"
}

# Function to change email password
change_email_password() {
    local username=$1
    local domain=$2
    local new_password=$3
    
    # Change password
    echo "${username}@${domain}:${new_password}" | chpasswd
    
    echo -e "${GREEN}Password changed for ${username}@${domain}${NC}"
}

# Function to update email quota
update_email_quota() {
    local username=$1
    local domain=$2
    local new_quota=$3
    
    # Update quota
    setquota -u "${username}@${domain}" 0 ${new_quota} 0 0 /var/mail
    
    echo -e "${GREEN}Quota updated for ${username}@${domain}${NC}"
}

# Main script
case "$1" in
    create)
        if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
            echo "Usage: $0 create <username> <domain> <password> [quota]"
            exit 1
        fi
        create_email_account "$2" "$3" "$4" "$5"
        ;;
    remove)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 remove <username> <domain>"
            exit 1
        fi
        remove_email_account "$2" "$3"
        ;;
    password)
        if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
            echo "Usage: $0 password <username> <domain> <new_password>"
            exit 1
        fi
        change_email_password "$2" "$3" "$4"
        ;;
    quota)
        if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
            echo "Usage: $0 quota <username> <domain> <new_quota>"
            exit 1
        fi
        update_email_quota "$2" "$3" "$4"
        ;;
    *)
        echo "Usage: $0 {create|remove|password|quota} [username] [domain] [password/quota]"
        exit 1
        ;;
esac

exit 0 