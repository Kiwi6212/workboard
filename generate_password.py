"""Generate a bcrypt password hash for WB_PASSWORD_HASH env var."""
import bcrypt
import getpass

pwd = getpass.getpass("Mot de passe : ")
print(bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode())
