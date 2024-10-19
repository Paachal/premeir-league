import secrets

# Generate a random secret key
secret_key = secrets.token_urlsafe(32)  # Generates a secure random key
print(secret_key)
