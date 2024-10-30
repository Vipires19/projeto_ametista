import pickle
from pathlib import Path
import bcrypt


def hash_passwords(password):
  salt = bcrypt.gensalt()
  hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

  return hashed.decode('utf-8')




if __name__ == "__main__":

  name = ["Admin"]
  email = ['admin@gmail.com']
  username = ["admin"]
  passwords = ["admin123"]

  hashed_passwords = [hash_passwords(password) for password in passwords]

  file_path = Path(__file__).parent/"hashed_pw.pkl"

  with file_path.open("wb") as file:
    pickle.dump(hashed_passwords, file)