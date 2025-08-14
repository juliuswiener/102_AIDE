import time, sys

def main():
    print("worker stub: starting heartbeats", flush=True)
    for _ in range(3):
        print("worker stub: heartbeat", flush=True)
        time.sleep(0.5)
    print("worker stub: exiting", flush=True)

if __name__ == "__main__":
    sys.exit(main())
