from GameRipper_Ultimate import run_scrapers, init_db
import threading

if __name__ == '__main__':
    init_db()
    threading.Thread(target=run_scrapers).start()
