"""Read-only connection test; never prints the password."""
import database

def main():
    try:
        with database.connect() as conn:
            print(conn.execute('SELECT VERSION()').fetchone()[0])
        print('Aiven connection successful.')
    except database.Error as exc:
        print('Connection failed. Check your internet, Aiven service status, and .env details.')
        print(type(exc).__name__)
        raise SystemExit(1)

if __name__ == '__main__':
    main()
